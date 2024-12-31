from models.database import Database

class User:
    def __init__(self, id=None, email=None, name=None):
        self.id = id
        self.email = email
        self.name = name
        self.db = Database()

    @classmethod
    def get_by_email(cls, email):
        db = Database()
        result = db.execute_one("SELECT * FROM users WHERE email = %s", (email,))
        if result:
            return cls(id=result['id'], email=result['email'], name=result['name'])
        return None

    def create(self):
        result = self.db.execute_one(
            "INSERT INTO users (email, name) VALUES (%s, %s) RETURNING id",
            (self.email, self.name)
        )
        self.id = result['id']
        return self

    def get_profile(self):
        return self.db.execute_one(
            "SELECT * FROM profiles WHERE user_id = %s",
            (self.id,)
        )

    def update_profile(self, gpa=None, interests=None, activities=None, 
                      target_majors=None, target_schools=None):
        self.db.execute(
            """
            INSERT INTO profiles (user_id, gpa, interests, activities, 
                                target_majors, target_schools)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                gpa = EXCLUDED.gpa,
                interests = EXCLUDED.interests,
                activities = EXCLUDED.activities,
                target_majors = EXCLUDED.target_majors,
                target_schools = EXCLUDED.target_schools,
                updated_at = CURRENT_TIMESTAMP
            """,
            (self.id, gpa, interests, activities, target_majors, target_schools)
        )

    def get_chat_sessions(self):
        return self.db.execute(
            "SELECT * FROM chat_sessions WHERE user_id = %s ORDER BY created_at DESC",
            (self.id,)
        )
