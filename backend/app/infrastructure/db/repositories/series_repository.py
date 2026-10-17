import logging
from typing import List, Tuple
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from app.infrastructure.db.query_filters import published_only
from app.domain.series.entities import SeriesCreate, SeriesUpdate, SeasonCreate, SeasonUpdate, EpisodeCreate, EpisodeUpdate

logger = logging.getLogger(__name__)

class SeriesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Series ---
    async def get_all_series(self, skip: int = 0, limit: int = 100, category_id: int | None = None, page_id: int | None = None, exclude_paged: bool = False, publish_status: str | None = None) -> Tuple[List[SeriesModel], int]:
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories),
            selectinload(SeriesModel.pages),
            selectinload(SeriesModel.source)
        )
        if publish_status == "published":
            stmt = published_only(stmt, SeriesModel)
        elif publish_status is not None:
            stmt = stmt.filter(SeriesModel.publish_status == publish_status)
        
        if category_id:
            stmt = stmt.filter(SeriesModel.categories.any(id=category_id))
        if page_id:
            stmt = stmt.filter(SeriesModel.pages.any(id=page_id))
        elif exclude_paged:
            stmt = stmt.filter(
                ~SeriesModel.pages.any(),
                ~SeriesModel.categories.any(CategoryModel.id == 2),
                ~SeriesModel.categories.any(CategoryModel.name.ilike("%anime%")),
                ~SeriesModel.title.ilike("%anime%")
            )

        total_stmt = select(func.count()).select_from(stmt.subquery())
        total = await self.session.scalar(total_stmt)
        
        stmt = stmt.order_by(SeriesModel.id.asc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total or 0

    async def search_series(self, title_query: str, skip: int = 0, limit: int = 100, publish_status: str | None = None) -> Tuple[List[SeriesModel], int]:
        clean_q = str(title_query).strip()
        code_q = clean_q.lstrip("#").strip()
        search_pattern = f"%{clean_q}%"
        
        conditions = [
            SeriesModel.title.ilike(search_pattern),
        ]
        if code_q != clean_q and code_q:
            conditions.append(SeriesModel.title.ilike(f"%{code_q}%"))

        target_num = code_q if code_q.isdigit() else (clean_q if clean_q.isdigit() else None)
        if target_num:
            conditions.append(SeriesModel.id == int(target_num))
        elif code_q.lower().startswith("s_") and code_q[2:].isdigit():
            conditions.append(SeriesModel.id == int(code_q[2:]))
        elif code_q.lower().startswith("s") and code_q[1:].isdigit():
            conditions.append(SeriesModel.id == int(code_q[1:]))

        stmt_where = or_(*conditions)
        if publish_status == "published":
            stmt_where = and_(stmt_where, SeriesModel.publish_status == "published")
        elif publish_status is not None:
            stmt_where = and_(stmt_where, SeriesModel.publish_status == publish_status)

        total_stmt = select(func.count(SeriesModel.id)).where(stmt_where)
        total = await self.session.scalar(total_stmt)
        
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories),
            selectinload(SeriesModel.pages),
            selectinload(SeriesModel.source)
        ).where(stmt_where).order_by(SeriesModel.id.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total or 0


    async def get_series_by_id(self, series_id: int, publish_status: str | None = None) -> SeriesModel | None:
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories),
            selectinload(SeriesModel.pages),
            selectinload(SeriesModel.source)
        ).where(SeriesModel.id == series_id)
        if publish_status == "published":
            stmt = published_only(stmt, SeriesModel)
        elif publish_status is not None:
            stmt = stmt.where(SeriesModel.publish_status == publish_status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_series_by_code(self, code: str, publish_status: str | None = None) -> SeriesModel | None:
        clean_code = str(code).strip()
        series_id = None
        if clean_code.isdigit():
            series_id = int(clean_code)
        elif clean_code.lower().startswith("s_") and clean_code[2:].isdigit():
            series_id = int(clean_code[2:])
        elif clean_code.lower().startswith("s") and clean_code[1:].isdigit():
            series_id = int(clean_code[1:])
        elif clean_code.lower().startswith("series_") and clean_code[7:].isdigit():
            series_id = int(clean_code[7:])
        elif clean_code.lower().startswith("serial_") and clean_code[7:].isdigit():
            series_id = int(clean_code[7:])
            
        if series_id is not None:
            return await self.get_series_by_id(series_id, publish_status=publish_status)
        return None


    async def get_series_by_source(self, chat_id: int, topic_id: int | None) -> SeriesModel | None:
        if topic_id is None:
            raise ValueError("topic_id is mandatory for get_series_by_source")
        from app.infrastructure.db.models.source import SourceModel
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories),
            selectinload(SeriesModel.pages),
            selectinload(SeriesModel.source)
        ).join(SourceModel, SeriesModel.source_id == SourceModel.id).where(
            SourceModel.chat_id == chat_id,
            SourceModel.topic_id == topic_id
        )
        result = await self.session.execute(stmt)
        models = list(result.scalars().all())

        # Ham serial ham kino mavjudligini tekshirish
        from app.infrastructure.db.models.movie import MovieModel
        from app.infrastructure.db.session import async_session_factory
        from app.core.admission_gate import record_rejection

        stmt_m = select(MovieModel).where(
            MovieModel.source_chat_id == chat_id,
            MovieModel.source_topic_id == topic_id,
        )
        res_m = await self.session.execute(stmt_m)
        movie_models = list(res_m.scalars().all())

        if len(models) > 1 or (len(models) >= 1 and len(movie_models) >= 1):
            defect_msg = f"Ambiguous topic: multiple entities ({len(models)} series, {len(movie_models)} movies) found for chat_id={chat_id}, topic_id={topic_id}"
            try:
                async with async_session_factory() as reject_session:
                    await record_rejection(
                        session=reject_session,
                        media_type="series",
                        source="auto_index",
                        source_key=f"{chat_id}:{topic_id}",
                        title=f"Ambiguous topic {chat_id}:{topic_id}",
                        payload={"chat_id": chat_id, "topic_id": topic_id, "series_count": len(models), "movie_count": len(movie_models)},
                        defects=[{"field": "topic_id", "defect": "ambiguous_topic", "reason": defect_msg}],
                        status="rejected"
                    )
                    await reject_session.commit()
            except Exception as e:
                logger.warning(f"Could not record rejection in independent session: {e}")
            raise ValueError(defect_msg)

        if len(models) == 0:
            return None
        return models[0]

    async def get_series_by_title_and_year(self, title: str, release_year: int | None = None) -> SeriesModel | None:
        clean_title = str(title).strip().lower()
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories),
            selectinload(SeriesModel.pages),
            selectinload(SeriesModel.source)
        ).where(func.lower(SeriesModel.title) == clean_title)
        if release_year:
            stmt = stmt.where(SeriesModel.release_year == release_year)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def create_series(self, series_data: SeriesCreate | dict) -> SeriesModel:
        if isinstance(series_data, dict):
            data = series_data.copy()
            category_ids = data.pop("category_ids", None)
            page_ids = data.pop("page_ids", None)
        else:
            category_ids = getattr(series_data, "category_ids", None)
            page_ids = getattr(series_data, "page_ids", None)
            data = series_data.model_dump(exclude={"category_ids", "page_ids"}, exclude_unset=True)
        
        series = SeriesModel(**data)
        
        if category_ids:
            result = await self.session.execute(select(CategoryModel).where(CategoryModel.id.in_(category_ids)))
            categories = result.scalars().all()
            series.categories = list(categories)
            
        if page_ids:
            from app.infrastructure.db.models.page import PageModel
            result = await self.session.execute(select(PageModel).where(PageModel.id.in_(page_ids)))
            pages = result.scalars().all()
            series.pages = list(pages)
            
        self.session.add(series)
        await self.session.flush()
        return await self.get_series_by_id(series.id)

    async def update_series(self, series_id: int, update_data: SeriesUpdate | dict) -> SeriesModel | None:
        series = await self.get_series_by_id(series_id)
        if not series:
            return None
        
        data = update_data if isinstance(update_data, dict) else update_data.model_dump(exclude={"category_ids", "page_ids"}, exclude_unset=True)
        
        category_ids = data.pop("category_ids", None) if isinstance(update_data, dict) else update_data.category_ids
        page_ids = data.pop("page_ids", None) if isinstance(update_data, dict) else update_data.page_ids
        
        for key, value in data.items():
            setattr(series, key, value)
            
        # Update category_ids from dict or model
        if category_ids is not None:
            result = await self.session.execute(select(CategoryModel).where(CategoryModel.id.in_(category_ids)))
            categories = result.scalars().all()
            series.categories = list(categories)
            
        if page_ids is not None:
            from app.infrastructure.db.models.page import PageModel
            result = await self.session.execute(select(PageModel).where(PageModel.id.in_(page_ids)))
            pages = result.scalars().all()
            series.pages = list(pages)
            
        await self.session.flush()
        return await self.get_series_by_id(series.id)

    async def delete_series(self, series_id: int) -> bool:
        series = await self.get_series_by_id(series_id)
        if not series:
            return False
        await self.session.delete(series)
        await self.session.flush()
        return True

    # --- Seasons ---
    async def get_season_by_id(self, season_id: int, publish_status: str | None = None) -> SeasonModel | None:
        stmt = select(SeasonModel).options(selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations)).where(SeasonModel.id == season_id)
        if publish_status == "published":
            stmt = published_only(stmt, SeasonModel)
        elif publish_status is not None:
            stmt = stmt.join(SeriesModel, SeasonModel.series_id == SeriesModel.id).where(SeriesModel.publish_status == publish_status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_seasons_by_series(self, series_id: int, publish_status: str | None = None) -> List[SeasonModel]:
        stmt = select(SeasonModel).options(selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations)).where(SeasonModel.series_id == series_id).order_by(SeasonModel.season_number)
        if publish_status == "published":
            stmt = published_only(stmt, SeasonModel)
        elif publish_status is not None:
            stmt = stmt.join(SeriesModel, SeasonModel.series_id == SeriesModel.id).where(SeriesModel.publish_status == publish_status)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_season(self, season_data: SeasonCreate) -> SeasonModel:
        season = SeasonModel(**season_data.model_dump())
        self.session.add(season)
        await self.session.flush()
        return await self.get_season_by_id(season.id)

    async def update_season(self, season_id: int, update_data: SeasonUpdate) -> SeasonModel | None:
        season = await self.get_season_by_id(season_id)
        if not season:
            return None
            
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(season, key, value)
            
        await self.session.flush()
        return await self.get_season_by_id(season.id)
        
    async def delete_season(self, season_id: int) -> bool:
        season = await self.get_season_by_id(season_id)
        if not season:
            return False
        await self.session.delete(season)
        await self.session.flush()
        return True

    # --- Episodes ---
    async def get_episode_by_id(self, episode_id: int, publish_status: str | None = None) -> EpisodeModel | None:
        stmt = select(EpisodeModel).options(selectinload(EpisodeModel.translations)).where(EpisodeModel.id == episode_id)
        if publish_status == "published":
            stmt = published_only(stmt, EpisodeModel)
        elif publish_status is not None:
            stmt = stmt.join(SeasonModel, EpisodeModel.season_id == SeasonModel.id).join(SeriesModel, SeasonModel.series_id == SeriesModel.id).where(SeriesModel.publish_status == publish_status)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_episode_by_code(self, code: str, publish_status: str | None = None) -> EpisodeModel | None:
        clean_code = str(code).strip()
        norm_code = clean_code.lower().replace("-", "").replace(" ", "").replace("_", "")
        db_norm = func.replace(func.replace(func.replace(func.lower(EpisodeModel.display_code), "-", ""), " ", ""), "_", "")
        
        where_conditions = [
            func.lower(EpisodeModel.code) == func.lower(clean_code),
            func.lower(EpisodeModel.display_code) == func.lower(clean_code),
            db_norm == norm_code
        ]
        if clean_code.isdigit():
            where_conditions.append(EpisodeModel.id == int(clean_code))

        stmt = select(EpisodeModel).options(selectinload(EpisodeModel.translations)).where(or_(*where_conditions))
        if publish_status == "published":
            stmt = published_only(stmt, EpisodeModel)
        elif publish_status is not None:
            stmt = stmt.join(SeasonModel, EpisodeModel.season_id == SeasonModel.id).join(SeriesModel, SeasonModel.series_id == SeriesModel.id).where(SeriesModel.publish_status == publish_status)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_episode_with_context_by_code(self, code: str, publish_status: str | None = None):
        """
        Bitta SQL so'rovida episode + uning season + series + barcha episodlarini yuklaydi.
        Bu get_episode_detail_by_code uchun N+1 muammosini bartaraf etadi.
        Returns: (episode, season, series) yoki (None, None, None)
        """
        clean_code = str(code).strip()
        code_conds = [func.lower(EpisodeModel.code) == func.lower(clean_code)]
        if clean_code.isdigit():
            code_conds.append(EpisodeModel.id == int(clean_code))

        # 1. Episode + translations: Birinchi navbatda unikal kod (code) yoki ID bo'yicha qidiramiz
        stmt = (
            select(EpisodeModel)
            .options(selectinload(EpisodeModel.translations))
            .where(or_(*code_conds))
        )
        result = await self.session.execute(stmt)
        episode = result.scalars().first()

        # Agar unikal kod bo'yicha topilmasa, display_code bo'yicha qidiramiz
        if not episode:
            norm_code = clean_code.lower().replace("-", "").replace(" ", "").replace("_", "")
            db_norm = func.replace(func.replace(func.replace(func.lower(EpisodeModel.display_code), "-", ""), " ", ""), "_", "")
            stmt_disp = (
                select(EpisodeModel)
                .options(selectinload(EpisodeModel.translations))
                .where(or_(
                    func.lower(EpisodeModel.display_code) == func.lower(clean_code),
                    db_norm == norm_code
                ))
            )
            res_disp = await self.session.execute(stmt_disp)
            episode = res_disp.scalars().first()

        if not episode:
            return None, None, None


        # 2. Season + uning barcha episodes (navigatsiya uchun)
        season_stmt = (
            select(SeasonModel)
            .options(
                selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations)
            )
            .where(SeasonModel.id == episode.season_id)
        )
        season_result = await self.session.execute(season_stmt)
        season = season_result.scalar_one_or_none()
        if not season:
            return episode, None, None

        # 3. Series + barcha seasons va episodes (prev/next navigatsiya uchun)
        series_stmt = (
            select(SeriesModel)
            .options(
                selectinload(SeriesModel.seasons)
                .selectinload(SeasonModel.episodes)
                .selectinload(EpisodeModel.translations),
                selectinload(SeriesModel.categories),
                selectinload(SeriesModel.source)
            )
            .where(SeriesModel.id == season.series_id)
        )
        series_result = await self.session.execute(series_stmt)
        series = series_result.scalar_one_or_none()

        if publish_status is not None:
            if not series or series.publish_status != publish_status:
                return None, None, None

        return episode, season, series

    async def get_episodes_by_season(self, season_id: int) -> List[EpisodeModel]:
        stmt = select(EpisodeModel).where(EpisodeModel.season_id == season_id).order_by(EpisodeModel.episode_number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_episode(self, episode_data: dict) -> EpisodeModel:
        from sqlalchemy.exc import IntegrityError
        # Pre-check if episode with same (season_id, episode_number) already exists
        stmt = (
            select(EpisodeModel)
            .options(selectinload(EpisodeModel.translations))
            .where(
                EpisodeModel.season_id == episode_data["season_id"],
                EpisodeModel.episode_number == episode_data["episode_number"]
            )
        )
        res = await self.session.execute(stmt)
        existing = res.scalar_one_or_none()
        if existing:
            return existing

        try:
            episode = EpisodeModel(**episode_data)
            self.session.add(episode)
            await self.session.flush()
            return await self.get_episode_by_id(episode.id)
        except IntegrityError:
            await self.session.rollback()
            res = await self.session.execute(stmt)
            existing = res.scalar_one_or_none()
            if existing:
                return existing
            raise

    async def update_episode(self, episode_id: int, update_data: EpisodeUpdate | dict) -> EpisodeModel | None:
        episode = await self.get_episode_by_id(episode_id)
        if not episode:
            return None
            
        data = update_data if isinstance(update_data, dict) else update_data.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(episode, key, value)
            
        await self.session.flush()
        return await self.get_episode_by_id(episode.id)

    async def add_episode_translation(self, episode_id: int, language: str, telegram_file_id: str, storage_channel_message_id: int) -> EpisodeModel | None:
        from app.infrastructure.db.models.translation import MovieTranslationModel

        # 1. NO OVERWRITES: Mavjud qism videosi ustiga yozmaslik
        stmt = select(EpisodeTranslationModel).where(
            EpisodeTranslationModel.episode_id == episode_id,
            EpisodeTranslationModel.language == language
        )
        res = await self.session.execute(stmt)
        existing_tr = res.scalar_one_or_none()
        if existing_tr and (existing_tr.telegram_file_id or existing_tr.storage_channel_message_id):
            raise ValueError(f"Mavjud qism videosini almashtirish taqiqlangan (No overwrite): episode_id={episode_id}, lang={language}")

        # 2. CROSS-TITLE CHECK: Bir xil telegram_file_id yoki storage_channel_message_id boshqa nomga biriktirilgan bo'lmasligi kerak
        if telegram_file_id:
            m_stmt = select(MovieTranslationModel).where(
                MovieTranslationModel.telegram_file_id == telegram_file_id
            )
            m_tr = (await self.session.execute(m_stmt)).scalar_one_or_none()
            if m_tr:
                raise ValueError(f"Fayl kinoga biriktirilgan (attached to movie_id={m_tr.movie_id}): file_id={telegram_file_id}")

            other_ep_stmt = select(EpisodeTranslationModel).where(
                EpisodeTranslationModel.telegram_file_id == telegram_file_id,
                EpisodeTranslationModel.episode_id != episode_id
            )
            other_ep = (await self.session.execute(other_ep_stmt)).scalar_one_or_none()
            if other_ep:
                raise ValueError(f"Fayl boshqa qismga biriktirilgan (attached to episode_id={other_ep.episode_id}): file_id={telegram_file_id}")

        if storage_channel_message_id:
            m_msg_stmt = select(MovieTranslationModel).where(
                MovieTranslationModel.storage_channel_message_id == storage_channel_message_id
            )
            m_msg_tr = (await self.session.execute(m_msg_stmt)).scalar_one_or_none()
            if m_msg_tr:
                raise ValueError(f"Xabar kinoga biriktirilgan (attached to movie_id={m_msg_tr.movie_id}): msg_id={storage_channel_message_id}")

            other_ep_msg_stmt = select(EpisodeTranslationModel).where(
                EpisodeTranslationModel.storage_channel_message_id == storage_channel_message_id,
                EpisodeTranslationModel.episode_id != episode_id
            )
            other_ep_msg = (await self.session.execute(other_ep_msg_stmt)).scalar_one_or_none()
            if other_ep_msg:
                raise ValueError(f"Xabar boshqa qismga biriktirilgan (attached to episode_id={other_ep_msg.episode_id}): msg_id={storage_channel_message_id}")

        if existing_tr:
            existing_tr.telegram_file_id = telegram_file_id
            existing_tr.storage_channel_message_id = storage_channel_message_id
        else:
            translation = EpisodeTranslationModel(
                episode_id=episode_id,
                language=language,
                telegram_file_id=telegram_file_id,
                storage_channel_message_id=storage_channel_message_id
            )
            self.session.add(translation)
        await self.session.flush()
        return await self.get_episode_by_id(episode_id)

    async def update_episode_translation(self, translation_id: int, language: str) -> bool:
        model = await self.session.get(EpisodeTranslationModel, translation_id)
        if not model:
            return False
        model.language = language
        await self.session.flush()
        return True

    async def delete_episode_translation(self, translation_id: int) -> bool:
        model = await self.session.get(EpisodeTranslationModel, translation_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True

    async def delete_episode(self, episode_id: int) -> bool:
        episode = await self.get_episode_by_id(episode_id)
        if not episode:
            return False
        await self.session.delete(episode)
        await self.session.flush()
        return True

    async def reserve_episodes_atomic(self, season_id: int, items: list[dict]) -> list[dict]:
        """
        BOSQICH A: Atomik tarzda season qatorini qulflaydi (SELECT ... FOR UPDATE)
        va berilgan items (sorted by message_id) uchun episode_number'larni
        ketma-ket bazada yaratib/band qilib qaytaradi.
        Hech qanday tashqi network await bo'lmaydi.
        """
        import uuid

        # 1. Season qatorini FOR UPDATE bilan qulflash
        stmt = (
            select(SeasonModel)
            .where(SeasonModel.id == season_id)
            .with_for_update()
        )
        res = await self.session.execute(stmt)
        season = res.scalar_one_or_none()
        if not season:
            raise ValueError(f"Season with ID {season_id} not found")

        # 2. Mavjud barcha qismlarni o'qish (lock ichida, tarjimalari bilan birga)
        episodes_stmt = (
            select(EpisodeModel)
            .options(selectinload(EpisodeModel.translations))
            .where(EpisodeModel.season_id == season_id)
            .order_by(EpisodeModel.episode_number)
        )
        episodes_res = await self.session.execute(episodes_stmt)
        existing_episodes = list(episodes_res.scalars().all())
        existing_by_num = {e.episode_number: e for e in existing_episodes}
        existing_by_msg = {e.source_message_id: e for e in existing_episodes if e.source_message_id}

        # Mavjud qismlarga biriktirilgan telegram_file_id larni to'plash
        file_to_ep = {}
        for e in existing_episodes:
            for tr in e.translations:
                if tr.telegram_file_id:
                    file_to_ep[tr.telegram_file_id] = e

        current_max = max(existing_by_num.keys(), default=0)

        reserved_results = []

        for item in items:
            source_msg_id = item.get("source_message_id")
            explicit_ep = item.get("explicit_episode_number")
            telegram_file_id = item.get("telegram_file_id")
            title = item.get("title")

            # Qayta forward qilingan dublikat tekshiruvi (Re-forwarded duplicate check)
            duplicate_ep = None
            if source_msg_id and source_msg_id in existing_by_msg:
                duplicate_ep = existing_by_msg[source_msg_id]
            elif telegram_file_id and telegram_file_id in file_to_ep:
                duplicate_ep = file_to_ep[telegram_file_id]

            if duplicate_ep is not None:
                # Dublikat: yangi qism YARATILMAYDI va qayta indekslanmaydi
                reserved_results.append({
                    "id": duplicate_ep.id,
                    "episode_number": duplicate_ep.episode_number,
                    "code": duplicate_ep.code,
                    "display_code": duplicate_ep.display_code,
                    "source_message_id": source_msg_id,
                    "season_number": season.season_number,
                    "is_update": False,
                    "is_duplicate": True
                })
                continue

            if explicit_ep is not None:
                ep_num = explicit_ep
                current_max = max(current_max, ep_num)
            else:
                current_max += 1
                ep_num = current_max

            if ep_num in existing_by_num:
                ep = existing_by_num[ep_num]
                # Agar ushbu qismda allaqachon video bo'lsa, uni almashtirmaslik kerak (No overwrite)
                has_video = any(tr.telegram_file_id or tr.storage_channel_message_id for tr in ep.translations)
                if has_video:
                    reserved_results.append({
                        "id": ep.id,
                        "episode_number": ep.episode_number,
                        "code": ep.code,
                        "display_code": ep.display_code,
                        "source_message_id": source_msg_id,
                        "season_number": season.season_number,
                        "is_update": True,
                        "is_duplicate": True
                    })
                    continue

                if source_msg_id:
                    ep.source_message_id = source_msg_id
                is_update = True
            else:
                code = uuid.uuid4().hex[:8]
                display_code = f"S{season.season_number}-CH{ep_num}"
                ep = EpisodeModel(
                    season_id=season_id,
                    episode_number=ep_num,
                    code=code,
                    display_code=display_code,
                    title=title or f"{ep_num}-qism",
                    source_message_id=source_msg_id
                )
                self.session.add(ep)
                existing_by_num[ep_num] = ep
                if source_msg_id:
                    existing_by_msg[source_msg_id] = ep
                is_update = False

            await self.session.flush()

            reserved_results.append({
                "id": ep.id,
                "episode_number": ep.episode_number,
                "code": ep.code,
                "display_code": ep.display_code,
                "source_message_id": source_msg_id,
                "season_number": season.season_number,
                "is_update": is_update,
                "is_duplicate": False
            })

        return reserved_results

