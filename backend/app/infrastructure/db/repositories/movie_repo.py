"""
Concrete implementation of IMovieRepository.
"""
import logging
from typing import Sequence
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

logger = logging.getLogger(__name__)

from app.domain.movies.entities import Movie
from app.domain.movies.repository import IMovieRepository
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.models.translation import MovieTranslationModel
from app.infrastructure.db.query_filters import published_only


class MovieRepositoryImpl(IMovieRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_domain(self, model: MovieModel) -> Movie:
        return Movie.model_validate(model)

    async def create(self, movie: Movie, category_ids: list[int] | None = None, page_ids: list[int] | None = None) -> Movie:
        model = MovieModel(**movie.model_dump(exclude={"id", "created_at", "updated_at", "categories", "translations", "pages"}, exclude_unset=True))
        
        if category_ids:
            result = await self.session.execute(select(CategoryModel).where(CategoryModel.id.in_(category_ids)))
            categories = result.scalars().all()
            model.categories = list(categories)
            
        if page_ids:
            from app.infrastructure.db.models.page import PageModel
            result = await self.session.execute(select(PageModel).where(PageModel.id.in_(page_ids)))
            pages = result.scalars().all()
            model.pages = list(pages)
            
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)

        # Automatic franchise canonical placement
        try:
            from app.core.franchise_canon import find_canon_match
            from app.infrastructure.db.models.collection import CollectionModel, CollectionItemModel
            canon_match = find_canon_match(model.tmdb_id, model.title)
            if not canon_match and model.original_title:
                canon_match = find_canon_match(model.tmdb_id, model.original_title)

            if canon_match:
                f_slug, canon_item = canon_match
                col_res = await self.session.execute(select(CollectionModel).where(CollectionModel.slug == f_slug))
                col = col_res.scalar_one_or_none()
                if col:
                    ci_res = await self.session.execute(
                        select(CollectionItemModel).where(
                            CollectionItemModel.collection_id == col.id,
                            or_(
                                CollectionItemModel.movie_id == model.id,
                                CollectionItemModel.chronological_order == canon_item["chronological_order"],
                            ),
                        )
                    )
                    if not ci_res.scalar_one_or_none():
                        new_ci = CollectionItemModel(
                            collection_id=col.id,
                            movie_id=model.id,
                            chronological_order=canon_item["chronological_order"],
                            release_order=canon_item["release_order"],
                            timeline_event_desc=canon_item["timeline_event_desc"],
                            is_locked=False,
                        )
                        self.session.add(new_ci)
                        await self.session.flush()
        except Exception as e:
            logger.warning(f"Avtomatik franshiza kanonik joylashtirishda xatolik: {e}")

        return self._to_domain(model)

    async def get_by_id(self, movie_id: int, publish_status: str | None = None) -> Movie | None:
        stmt = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations),
            selectinload(MovieModel.pages)
        ).where(MovieModel.id == movie_id)
        if publish_status == "published":
            stmt = published_only(stmt, MovieModel)
        elif publish_status is not None and publish_status != "all":
            stmt = stmt.where(MovieModel.publish_status == publish_status)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_domain(model) if model else None

    async def get_by_code(self, code: str, publish_status: str | None = None) -> Movie | None:
        clean_code = code.strip()
        where_conditions = [
            func.lower(MovieModel.code) == func.lower(clean_code)
        ]
        if clean_code.isdigit():
            where_conditions.append(MovieModel.id == int(clean_code))

        stmt = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations),
            selectinload(MovieModel.pages)
        ).where(or_(*where_conditions))
        if publish_status == "published":
            stmt = published_only(stmt, MovieModel)
        elif publish_status is not None and publish_status != "all":
            stmt = stmt.where(MovieModel.publish_status == publish_status)
        result = await self.session.execute(stmt)
        model = result.scalars().first()
        return self._to_domain(model) if model else None


    async def get_by_source(self, chat_id: int, topic_id: int | None = None) -> Movie | None:
        if topic_id is None:
            raise ValueError("topic_id is mandatory for get_by_source")
        stmt = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations),
            selectinload(MovieModel.pages)
        ).where(
            MovieModel.source_chat_id == chat_id,
            MovieModel.source_topic_id == topic_id
        )
        result = await self.session.execute(stmt)
        models = list(result.scalars().all())

        # Ham kino ham serial manbasi borligini tekshirish
        from app.infrastructure.db.models.source import SourceModel
        from app.infrastructure.db.session import async_session_factory
        from app.core.admission_gate import record_rejection

        stmt_s = select(SourceModel).where(
            SourceModel.chat_id == chat_id,
            SourceModel.topic_id == topic_id,
        )
        res_s = await self.session.execute(stmt_s)
        series_sources = list(res_s.scalars().all())

        if len(models) > 1 or (len(models) >= 1 and len(series_sources) >= 1):
            defect_msg = f"Ambiguous topic: multiple entities ({len(models)} movies, {len(series_sources)} series) found for chat_id={chat_id}, topic_id={topic_id}"
            try:
                async with async_session_factory() as reject_session:
                    await record_rejection(
                        session=reject_session,
                        media_type="movie",
                        source="auto_index",
                        source_key=f"{chat_id}:{topic_id}",
                        title=f"Ambiguous topic {chat_id}:{topic_id}",
                        payload={"chat_id": chat_id, "topic_id": topic_id, "movie_count": len(models), "series_count": len(series_sources)},
                        defects=[{"field": "topic_id", "defect": "ambiguous_topic", "reason": defect_msg}],
                        status="rejected"
                    )
                    await reject_session.commit()
            except Exception as e:
                logger.warning(f"Could not record rejection in independent session: {e}")
            raise ValueError(defect_msg)

        if len(models) == 0:
            return None
        return self._to_domain(models[0])

    async def search_by_title(self, title_query: str, skip: int = 0, limit: int = 20, publish_status: str | None = None) -> tuple[Sequence[Movie], int]:
        clean_q = str(title_query).strip()
        code_q = clean_q.lstrip("#").strip()
        conditions = [
            MovieModel.title.ilike(f"%{clean_q}%"),
            MovieModel.original_title.ilike(f"%{clean_q}%"),
        ]
        if code_q:
            conditions.append(MovieModel.code.ilike(f"%{code_q}%"))
            if code_q.isdigit():
                conditions.append(MovieModel.id == int(code_q))
        elif clean_q.isdigit():
            conditions.append(MovieModel.id == int(clean_q))

        query = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations),
            selectinload(MovieModel.pages)
        ).where(or_(*conditions))
        if publish_status == "published":
            query = published_only(query, MovieModel)
        elif publish_status is not None and publish_status != "all":
            query = query.filter(MovieModel.publish_status == publish_status)
        
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        result = await self.session.execute(query.order_by(MovieModel.id.desc()).offset(skip).limit(limit))
        models = result.scalars().all()
        
        return [self._to_domain(m) for m in models], total or 0

    async def list_movies(self, skip: int = 0, limit: int = 20, category_id: int | None = None, page_id: int | None = None, exclude_paged: bool = False, publish_status: str | None = None) -> tuple[Sequence[Movie], int]:
        query = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations),
            selectinload(MovieModel.pages)
        )
        if publish_status == "published":
            query = published_only(query, MovieModel)
        elif publish_status is not None and publish_status != "all":
            query = query.filter(MovieModel.publish_status == publish_status)

        if category_id:
            query = query.filter(MovieModel.categories.any(id=category_id))
        
        if page_id:
            query = query.filter(MovieModel.pages.any(id=page_id))
        elif exclude_paged:
            query = query.filter(
                ~MovieModel.pages.any(),
                ~MovieModel.categories.any(CategoryModel.id == 2),
                ~MovieModel.categories.any(CategoryModel.name.ilike("%anime%")),
                ~MovieModel.title.ilike("%anime%")
            )
            
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)
        
        result = await self.session.execute(query.order_by(MovieModel.id.asc()).offset(skip).limit(limit))
        models = result.scalars().all()
        
        return [self._to_domain(m) for m in models], total or 0

    async def update(self, movie: Movie, category_ids: list[int] | None = None, page_ids: list[int] | None = None) -> Movie:
        model = await self.session.get(MovieModel, movie.id)
        if not model:
            raise ValueError(f"Movie with id {movie.id} not found")
            
        update_data = movie.model_dump(exclude={"id", "created_at", "updated_at", "categories", "translations", "pages"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
            
        if category_ids is not None:
            result = await self.session.execute(select(CategoryModel).where(CategoryModel.id.in_(category_ids)))
            categories = result.scalars().all()
            model.categories = list(categories)
            
        if page_ids is not None:
            from app.infrastructure.db.models.page import PageModel
            result = await self.session.execute(select(PageModel).where(PageModel.id.in_(page_ids)))
            pages = result.scalars().all()
            model.pages = list(pages)
            
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain(model)

    async def delete(self, movie_id: int) -> bool:
        model = await self.session.get(MovieModel, movie_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True

    async def add_translation(self, movie_id: int, language: str, telegram_file_id: str, storage_channel_message_id: int, allow_replace: bool = False) -> Movie | None:
        from app.infrastructure.db.models.translation import EpisodeTranslationModel

        # 1. NO OVERWRITES: Mavjud tarjima ustiga yozmaslik (faqat allow_replace=True bo'lganda ruxsat etiladi)
        stmt = select(MovieTranslationModel).where(
            MovieTranslationModel.movie_id == movie_id,
            MovieTranslationModel.language == language
        )
        res = await self.session.execute(stmt)
        existing_tr = res.scalar_one_or_none()
        if not allow_replace and existing_tr and (existing_tr.telegram_file_id or existing_tr.storage_channel_message_id):
            raise ValueError(f"Mavjud kino tarjimasini almashtirish taqiqlangan (No overwrite): movie_id={movie_id}, lang={language}")

        # 2. CROSS-TITLE CHECK: Bir xil telegram_file_id yoki storage_channel_message_id boshqa nomga biriktirilgan bo'lmasligi kerak
        if telegram_file_id:
            other_m_stmt = select(MovieTranslationModel).where(
                MovieTranslationModel.telegram_file_id == telegram_file_id,
                MovieTranslationModel.movie_id != movie_id
            )
            other_m = (await self.session.execute(other_m_stmt)).scalar_one_or_none()
            if other_m:
                raise ValueError(f"Fayl boshqa kinoga biriktirilgan (attached to movie_id={other_m.movie_id}): file_id={telegram_file_id}")

            ep_stmt = select(EpisodeTranslationModel).where(
                EpisodeTranslationModel.telegram_file_id == telegram_file_id
            )
            ep_tr = (await self.session.execute(ep_stmt)).scalar_one_or_none()
            if ep_tr:
                raise ValueError(f"Fayl serial qismiga biriktirilgan (attached to episode_id={ep_tr.episode_id}): file_id={telegram_file_id}")

        if storage_channel_message_id:
            other_msg_stmt = select(MovieTranslationModel).where(
                MovieTranslationModel.storage_channel_message_id == storage_channel_message_id,
                MovieTranslationModel.movie_id != movie_id
            )
            other_msg = (await self.session.execute(other_msg_stmt)).scalar_one_or_none()
            if other_msg:
                raise ValueError(f"Xabar boshqa kinoga biriktirilgan (attached to movie_id={other_msg.movie_id}): msg_id={storage_channel_message_id}")

            ep_msg_stmt = select(EpisodeTranslationModel).where(
                EpisodeTranslationModel.storage_channel_message_id == storage_channel_message_id
            )
            ep_msg_tr = (await self.session.execute(ep_msg_stmt)).scalar_one_or_none()
            if ep_msg_tr:
                raise ValueError(f"Xabar serial qismiga biriktirilgan (attached to episode_id={ep_msg_tr.episode_id}): msg_id={storage_channel_message_id}")

        if existing_tr:
            existing_tr.telegram_file_id = telegram_file_id
            existing_tr.storage_channel_message_id = storage_channel_message_id
        else:
            translation = MovieTranslationModel(
                movie_id=movie_id,
                language=language,
                telegram_file_id=telegram_file_id,
                storage_channel_message_id=storage_channel_message_id
            )
            self.session.add(translation)
        await self.session.flush()
        return await self.get_by_id(movie_id)

    async def delete_translation(self, translation_id: int) -> bool:
        model = await self.session.get(MovieTranslationModel, translation_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True
