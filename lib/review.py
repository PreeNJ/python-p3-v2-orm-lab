# lib/review.py

from lib import CONN, CURSOR
from lib.employee import Employee

class Review:
    all = {}

    def __init__(self, year, summary, employee_id, id=None):
        self._year = None
        self._summary = None
        self._employee_id = None

        # run through the property setters for validation
        self.year = year
        self.summary = summary
        self.employee_id = employee_id

        self.id = id

    def __repr__(self):
        return (f"<Review id={self.id} year={self.year} "
                f"employee_id={self.employee_id!r} summary={self.summary!r}>")

    @classmethod
    def create_table(cls):
        sql = """
        CREATE TABLE IF NOT EXISTS reviews (
          id INTEGER PRIMARY KEY,
          year INTEGER,
          summary TEXT,
          employee_id INTEGER,
          FOREIGN KEY(employee_id) REFERENCES employees(id)
        );
        """
        CURSOR.execute(sql)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        CURSOR.execute("DROP TABLE IF EXISTS reviews;")
        CONN.commit()

    def save(self):
        if self.id:
            return self.update()

        sql = "INSERT INTO reviews (year, summary, employee_id) VALUES (?, ?, ?);"
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id))
        CONN.commit()

        self.id = CURSOR.lastrowid
        Review.all[self.id] = self
        return self

    @classmethod
    def create(cls, year, summary, employee_id):
        review = cls(year, summary, employee_id)
        return review.save()

    @classmethod
    def instance_from_db(cls, row):
        id_, year, summary, emp_id = row
        if id_ in cls.all:
            inst = cls.all[id_]
            # refresh in-memory values
            inst._year = year
            inst._summary = summary
            inst._employee_id = emp_id
            return inst

        inst = cls(year, summary, emp_id, id=id_)
        cls.all[id_] = inst
        return inst

    @classmethod
    def find_by_id(cls, id):
        CURSOR.execute("SELECT * FROM reviews WHERE id = ?;", (id,))
        row = CURSOR.fetchone()
        return cls.instance_from_db(row) if row else None

    def update(self):
        if not self.id:
            raise ValueError("Cannot update a Review that hasn't been saved.")
        sql = """
        UPDATE reviews
        SET year = ?, summary = ?, employee_id = ?
        WHERE id = ?;
        """
        CURSOR.execute(sql, (self.year, self.summary, self.employee_id, self.id))
        CONN.commit()
        return self

    def delete(self):
        if not self.id:
            return
        CURSOR.execute("DELETE FROM reviews WHERE id = ?;", (self.id,))
        CONN.commit()
        Review.all.pop(self.id, None)
        self.id = None

    @classmethod
    def get_all(cls):
        CURSOR.execute("SELECT * FROM reviews;")
        rows = CURSOR.fetchall()
        return [cls.instance_from_db(row) for row in rows]

    # --- property validations ---

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, val):
        if not isinstance(val, int) or val < 2000:
            raise ValueError("year must be an integer >= 2000")
        self._year = val

    @property
    def summary(self):
        return self._summary

    @summary.setter
    def summary(self, val):
        if not isinstance(val, str) or not val.strip():
            raise ValueError("summary must be a non-empty string")
        self._summary = val.strip()

    @property
    def employee_id(self):
        return self._employee_id

    @employee_id.setter
    def employee_id(self, val):
        if not isinstance(val, int):
            raise ValueError("employee_id must be an integer")
        if Employee.find_by_id(val) is None:
            raise ValueError(f"No Employee with id={val} exists")
        self._employee_id = val
