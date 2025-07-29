import time
from typing import Any, Sequence
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

def save_batch(records: Sequence[Any], session: Session, max_attempts: int=5) -> None:
    if not records:
        print(f'No Records to insert into Database')
        return
    
    for attempts in range(1, max_attempts+1):
        try:
            session.bulk_save_objects(records)
            session.commit()
            return
        except OperationalError as e:
            if 'database is locked' in str(e):
                print(f'Database is locked, retrying commit ({attempts}/{max_attempts})')
                time.sleep((2**attempts)+1)
                continue
            else:
                print(f'Operational Error (non-lock): {e}')
                session.rollback()
                raise
        except SQLAlchemyError as e:
            print(f'SQLAlchemy Error: {e}')
            session.rollback()
            raise
        except Exception as e:
            print(f'Exception: {e}')
            session.rollback()
            raise
        finally:
            if attempts == max_attempts:
                session.close()
    print('[Failed to commit records in Database]')