from sqlalchemy import create_engine
from sqlalchemy import Engine
from sqlalchemy import Result
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker


class DatabaseConnection():
    def __init__(self, host: str, username: str, password: str, database: str,
                 engine: Engine = None, session: Session = None) -> None:
        self.host: str = host
        self.username: str = username
        self.password: str = password
        self.database: str = database
        self._engine: Engine = engine
        self._session: Session = session

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = create_engine(
                f'postgresql://{self.username}:{self.password}@{self.host}/{self.database}'
            )
        return self._engine

    @property
    def session(self) -> Session:
        if self._session is None:
            Session = sessionmaker(bind=self.engine)
            self._session = Session()
        return self._session

    def connect(self) -> None:
        try:
            self.engine  # Inicializa el engine si es None
            self.session  # Inicializa la sesión si es None
            self.session.connection()
            print('\033[32m', 'Connected to PostgreSQL database', '\033[0m')
        except Exception as error:
            print(f'Failed to connect to PostgreSQL database: {error}')

    def disconnect(self) -> None:
        if self.session:
            self.session.close()
            print('Disconnected from PostgreSQL database')

    def execute_query(self, query: str) -> Result | None:
        try:
            result = self.session.execute(text(query)).fetchall()
            return result
        except Exception as error:
            print(f'Failed to execute query: {error}')
            return None
