import os
import math
import asyncio
import hashlib
import inspect
import logging
from typing import Optional, List, Union, Tuple, BinaryIO, AsyncGenerator
from telethon import utils, helpers, TelegramClient
from telethon.crypto import AuthKey
from telethon.network import MTProtoSender
from telethon.tl.alltlobjects import LAYER
from telethon.tl.functions import InvokeWithLayerRequest
from telethon.tl.functions.auth import ExportAuthorizationRequest, ImportAuthorizationRequest
from telethon.tl.functions.upload import (
    GetFileRequest,
    SaveFilePartRequest,
    SaveBigFilePartRequest,
)
from telethon.tl.types import (
    Document,
    InputFileLocation,
    InputDocumentFileLocation,
    InputPhotoFileLocation,
    InputPeerPhotoFileLocation,
    TypeInputFile,
    InputFileBig,
    InputFile,
    Message,
)

logger = logging.getLogger(__name__)

TypeLocation = Union[
    Document,
    InputDocumentFileLocation,
    InputPeerPhotoFileLocation,
    InputFileLocation,
    InputPhotoFileLocation,
]


class DownloadSender:
    def __init__(
        self,
        client: TelegramClient,
        sender: MTProtoSender,
        file: TypeLocation,
        offset: int,
        limit: int,
        stride: int,
        count: int,
    ) -> None:
        self.sender = sender
        self.client = client
        self.request = GetFileRequest(file, offset=offset, limit=limit)
        self.stride = stride
        self.remaining = count

    async def next(self) -> Optional[bytes]:
        if not self.remaining:
            return None
        result = await asyncio.wait_for(self.client._call(self.sender, self.request), timeout=35.0)
        self.remaining -= 1
        self.request.offset += self.stride
        return result.bytes

    async def disconnect(self):
        return await self.sender.disconnect()


class UploadSender:
    def __init__(
        self,
        client: TelegramClient,
        sender: MTProtoSender,
        file_id: int,
        part_count: int,
        big: bool,
        index: int,
        stride: int,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        self.client = client
        self.sender = sender
        self.part_count = part_count
        if big:
            self.request = SaveBigFilePartRequest(file_id, index, part_count, b"")
        else:
            self.request = SaveFilePartRequest(file_id, index, b"")
        self.stride = stride
        self.previous = None
        self.loop = loop

    async def next(self, data: bytes) -> None:
        if self.previous:
            await self.previous
        self.previous = self.loop.create_task(self._next(data))

    async def _next(self, data: bytes) -> None:
        self.request.bytes = data
        await asyncio.wait_for(self.client._call(self.sender, self.request), timeout=45.0)
        self.request.file_part += self.stride

    async def disconnect(self) -> None:
        if self.previous:
            await self.previous
        return await self.sender.disconnect()


class ParallelTransferrer:
    def __init__(self, client: TelegramClient, dc_id: Optional[int] = None) -> None:
        self.client = client
        self.loop = self.client.loop
        self.dc_id = dc_id or self.client.session.dc_id
        self.auth_key = (
            None
            if dc_id and self.client.session.dc_id != dc_id
            else self.client.session.auth_key
        )
        self.senders: Optional[List[Union[DownloadSender, UploadSender]]] = None
        self.upload_ticker = 0

    async def _cleanup(self) -> None:
        if self.senders:
            await asyncio.gather(
                *[sender.disconnect() for sender in self.senders],
                return_exceptions=True,
            )
            self.senders = None

    @staticmethod
    def _get_connection_count(file_size: int, max_count: int = 5) -> int:
        if file_size > 50 * 1024 * 1024:
            return max_count
        return max(2, math.ceil((file_size / (50 * 1024 * 1024)) * max_count))

    async def _create_sender(self) -> MTProtoSender:
        dc = await self.client._get_dc(self.dc_id)
        sender = MTProtoSender(self.auth_key, loggers=self.client._log)
        proxy = getattr(self.client, "_proxy", None)
        local_addr = getattr(self.client, "_local_addr", None)
        conn = self.client._connection(
            dc.ip_address,
            dc.port,
            dc.id,
            loggers=self.client._log,
            proxy=proxy,
            local_addr=local_addr,
        )
        await sender.connect(conn)
        if not self.auth_key:
            auth = await self.client(ExportAuthorizationRequest(self.dc_id))
            self.client._init_request.query = ImportAuthorizationRequest(
                id=auth.id, bytes=auth.bytes
            )
            req = InvokeWithLayerRequest(LAYER, self.client._init_request)
            await sender.send(req)
            self.auth_key = sender.auth_key
        return sender

    async def _init_download(
        self, connections: int, file: TypeLocation, part_count: int, part_size: int
    ) -> None:
        minimum, remainder = divmod(part_count, connections)

        def get_part_count() -> int:
            nonlocal remainder
            if remainder > 0:
                remainder -= 1
                return minimum + 1
            return minimum

        first_sender = await self._create_download_sender(
            file, 0, part_size, connections * part_size, get_part_count()
        )
        other_senders = await asyncio.gather(
            *[
                self._create_download_sender(
                    file, i, part_size, connections * part_size, get_part_count()
                )
                for i in range(1, connections)
            ]
        )
        self.senders = [first_sender, *other_senders]

    async def _create_download_sender(
        self, file: TypeLocation, index: int, part_size: int, stride: int, part_count: int
    ) -> DownloadSender:
        return DownloadSender(
            self.client,
            await self._create_sender(),
            file,
            index * part_size,
            part_size,
            stride,
            part_count,
        )

    async def _init_upload(
        self, connections: int, file_id: int, part_count: int, big: bool
    ) -> None:
        first_sender = await self._create_upload_sender(file_id, part_count, big, 0, connections)
        other_senders = await asyncio.gather(
            *[
                self._create_upload_sender(file_id, part_count, big, i, connections)
                for i in range(1, connections)
            ]
        )
        self.senders = [first_sender, *other_senders]

    async def _create_upload_sender(
        self, file_id: int, part_count: int, big: bool, index: int, stride: int
    ) -> UploadSender:
        return UploadSender(
            self.client,
            await self._create_sender(),
            file_id,
            part_count,
            big,
            index,
            stride,
            loop=self.loop,
        )

    async def init_upload(
        self,
        file_id: int,
        file_size: int,
        part_size_kb: Optional[float] = None,
        connection_count: Optional[int] = None,
    ) -> Tuple[int, int, bool]:
        connection_count = connection_count or self._get_connection_count(file_size)
        part_size = int((part_size_kb or utils.get_appropriated_part_size(file_size)) * 1024)
        part_count = (file_size + part_size - 1) // part_size
        is_large = file_size > 10 * 1024 * 1024
        await self._init_upload(connection_count, file_id, part_count, is_large)
        return part_size, part_count, is_large

    async def upload(self, part: bytes) -> None:
        await self.senders[self.upload_ticker].next(part)
        self.upload_ticker = (self.upload_ticker + 1) % len(self.senders)

    async def finish_upload(self) -> None:
        await self._cleanup()

    async def download(
        self,
        file: TypeLocation,
        file_size: int,
        part_size_kb: Optional[float] = None,
        connection_count: Optional[int] = None,
    ) -> AsyncGenerator[bytes, None]:
        connection_count = connection_count or self._get_connection_count(file_size)
        part_size = int((part_size_kb or utils.get_appropriated_part_size(file_size)) * 1024)
        part_count = math.ceil(file_size / part_size)
        await self._init_download(connection_count, file, part_count, part_size)

        try:
            part = 0
            while part < part_count:
                tasks = [self.loop.create_task(s.next()) for s in self.senders]
                for task in tasks:
                    data = await task
                    if not data:
                        break
                    yield data
                    part += 1
        finally:
            await self._cleanup()


def _stream_file_chunks(file_obj: BinaryIO, chunk_size: int = 128 * 1024):
    while True:
        data = file_obj.read(chunk_size)
        if not data:
            break
        yield data


async def fast_upload_file(
    client: TelegramClient,
    file_path: str,
    progress_callback: callable = None,
    connection_count: Optional[int] = None,
    part_size_kb: Optional[float] = 512,
) -> Tuple[TypeInputFile, int]:
    """
    Katta fayllarni parallel MTProto oqimlari orqali juda yuqori tezlikda Telegramga yuklaydi.
    """
    file_size = os.path.getsize(file_path)
    file_id = helpers.generate_random_long()
    hash_md5 = hashlib.md5()

    uploader = ParallelTransferrer(client)
    part_size, part_count, is_large = await uploader.init_upload(
        file_id=file_id,
        file_size=file_size,
        part_size_kb=part_size_kb,
        connection_count=connection_count,
    )

    buffer = bytearray()
    uploaded_bytes = 0

    with open(file_path, "rb") as f:
        for chunk in _stream_file_chunks(f, chunk_size=min(part_size, 512 * 1024)):
            if not is_large:
                hash_md5.update(chunk)

            buffer.extend(chunk)
            if len(buffer) >= part_size:
                data_to_send = bytes(buffer[:part_size])
                await uploader.upload(data_to_send)
                uploaded_bytes += len(data_to_send)
                if progress_callback:
                    r = progress_callback(uploaded_bytes, file_size)
                    if inspect.isawaitable(r):
                        await r
                buffer = bytearray(buffer[part_size:])

        if len(buffer) > 0:
            data_to_send = bytes(buffer)
            await uploader.upload(data_to_send)
            uploaded_bytes += len(data_to_send)
            if progress_callback:
                r = progress_callback(uploaded_bytes, file_size)
                if inspect.isawaitable(r):
                    await r

    await uploader.finish_upload()

    if is_large:
        return InputFileBig(file_id, part_count, os.path.basename(file_path)), file_size
    else:
        return (
            InputFile(file_id, part_count, os.path.basename(file_path), hash_md5.hexdigest()),
            file_size,
        )


async def fast_download_media(
    client: TelegramClient,
    message: Message,
    out_path: str,
    progress_callback: callable = None,
    connection_count: Optional[int] = None,
    part_size_kb: Optional[float] = 512,
) -> str:
    """
    Telegram xabaridagi katta media faylni parallel MTProto oqimlari orqali juda yuqori tezlikda yuklab oladi.
    """
    doc = message.document or getattr(message.media, "document", None)
    if not doc:
        # Document bo'lmasa, standart usulga o'tamiz
        return await client.download_media(message, file=out_path, progress_callback=progress_callback)

    size = doc.size
    dc_id, location = utils.get_input_location(doc)

    downloader = ParallelTransferrer(client, dc_id=dc_id)
    downloaded_stream = downloader.download(
        file=location,
        file_size=size,
        connection_count=connection_count,
        part_size_kb=part_size_kb,
    )

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    downloaded_bytes = 0

    with open(out_path, "wb") as f:
        async for chunk in downloaded_stream:
            f.write(chunk)
            downloaded_bytes += len(chunk)
            if progress_callback:
                r = progress_callback(downloaded_bytes, size)
                if inspect.isawaitable(r):
                    await r

    return out_path


async def fast_download(
    client: TelegramClient,
    location_or_msg: Union[Message, TypeLocation],
    out_file_path: str,
    progress_callback: callable = None,
    connection_count: Optional[int] = None,
    part_size_kb: Optional[float] = 512,
) -> str:
    """
    Convenience wrapper accepting Message or Document/TypeLocation.
    """
    if isinstance(location_or_msg, Message):
        return await fast_download_media(client, location_or_msg, out_file_path, progress_callback, connection_count, part_size_kb)

    doc = getattr(location_or_msg, "document", location_or_msg)
    size = getattr(doc, "size", 0)
    dc_id, location = utils.get_input_location(doc)
    downloader = ParallelTransferrer(client, dc_id=dc_id)
    downloaded_stream = downloader.download(
        file=location,
        file_size=size,
        connection_count=connection_count,
        part_size_kb=part_size_kb,
    )
    os.makedirs(os.path.dirname(os.path.abspath(out_file_path)), exist_ok=True)
    downloaded_bytes = 0
    with open(out_file_path, "wb") as f:
        async for chunk in downloaded_stream:
            f.write(chunk)
            downloaded_bytes += len(chunk)
            if progress_callback:
                r = progress_callback(downloaded_bytes, size)
                if inspect.isawaitable(r):
                    await r
    return out_file_path


async def fast_upload(
    client: TelegramClient,
    file_path: str,
    progress_callback: callable = None,
    connection_count: Optional[int] = None,
    part_size_kb: Optional[float] = 512,
) -> TypeInputFile:
    """
    Convenience wrapper returning TypeInputFile directly.
    """
    res, _ = await fast_upload_file(client, file_path, progress_callback, connection_count, part_size_kb)
    return res
