# lib/employee.py

from lib import CONN, CURSOR
from lib.department import Department

class Employee:
    all = {}

    def __init__(self, name, title, department_id, id=None):
        self._name = None
        self._title = None
        self._department_id = None

        self.name = name
        self.title = title
        self.department_id = department_id

        self.id = id

    def __repr__(self):
        return (f"<Employee id={self.id} name={self.name!r} "
                f"title={self.title!r} department_id={self.department_id}>")

    @classmethod
    def create_table(cls):
        CURSOR.execute("""
        CREATE TABLE IF NOT EXISTS employees (
          id INTEGER PRIMARY KEY,
          name TEXT,
          title TEXT,
          department_id INTEGER,
          FOREIGN KEY(department_id) REFERENCES departments(id)
        );
        """)
        CONN.commit()

    @classmethod
    def drop_table(cls):
        CURSOR.execute("DROP TABLE IF EXISTS employees;")
        CONN.commit()

    def save(self):
        if self.id:
            return self.update()

        CURSOR.execute(
            "INSERT INTO employees (name, title, department_id) VALUES (?, ?, ?);",
            (self.name, self.title, self.department_id)
        )
        CONN.commit()

        self.id = CURSOR.lastrowid
        Employee.all[self.id] = self
        return self

    @classmethod
    def create(cls, name, title, department_id):
        return cls(name, title, department_id).save()

    @classmethod
    def instance_from_db(cls, row):
        id_, name, title, dep_id = row
        if id_ in cls.all:
            inst = cls.all[id_]
            inst._name = name
            inst._title = title
            inst._department_id = dep_id
            return inst

        inst = cls(name, title, dep_id, id=id_)
        cls.all[id_] = inst
        return inst

    @classmethod
    def find_by_id(cls, id):
        CURSOR.execute("SELECT * FROM employees WHERE id = ?;", (id,))
        row = CURSOR.fetchone()
        return cls.instance_from_db(row) if row else None

    @classmethod
    def find_by_name(cls, name):
        CURSOR.execute("SELECT * FROM employees WHERE name = ?;", (name,))
        row = CURSOR.fetchone()
        return cls.instance_from_db(row) if row else None

    def update(self):
        if not self.id:
            raise ValueError("Cannot update an Employee that hasn't been saved.")
        CURSOR.execute(
            "UPDATE employees SET name = ?, title = ?, department_id = ? WHERE id = ?;",
            (self.name, self.title, self.department_id, self.id)
        )
        CONN.commit()
        return self

    def delete(self):
        if not self.id:
            return
        CURSOR.execute("DELETE FROM employees WHERE id = ?;", (self.id,))
        CONN.commit()
        Employee.all.pop(self.id, None)
        self.id = None

    @classmethod
    def get_all(cls):
        CURSOR.execute("SELECT * FROM employees;")
        rows = CURSOR.fetchall()
        return [cls.instance_from_db(r) for r in rows]

    # --- property validations ---

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, val):
        if not isinstance(val, str) or not val.strip():
            raise ValueError("name must be a non-empty string")
        self._name = val.strip()

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, val):
        if not isinstance(val, str) or not val.strip():
            raise ValueError("title must be a non-empty string")
        self._title = val.strip()

    @property
    def department_id(self):
        return self._department_id

    @department_id.setter
    def department_id(self, val):
        if not isinstance(val, int):
            raise ValueError("department_id must be an integer")
        if Department.find_by_id(val) is None:
            raise ValueError(f"No Department with id={val} exists")
        self._department_id = val

    # --- NEW: pull in associated reviews ---
    def reviews(self):
        from lib.review import Review
        CURSOR.execute(
            "SELECT * FROM reviews WHERE employee_id = ?;",
            (self.id,)
        )
        rows = CURSOR.fetchall()
        return [Review.instance_from_db(row) for row in rows]
