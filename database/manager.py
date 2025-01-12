import aiosqlite


class DatabaseManager:
    def __init__(self, *, connection: aiosqlite.Connection) -> None:
        self.connection = connection

    async def add_warn(
        self, user_id: int, server_id: int, moderator_id: int, reason: str
    ) -> int:
        """
        Add a warn to the database.

        :param user_id: ID of the user to warn.
        :param server_id: ID of the server.
        :param moderator_id: ID of the moderator issuing the warn.
        :param reason: Reason for the warn.
        :return: The ID of the new warn.
        """
        cursor = await self.connection.execute(
            "SELECT id FROM warns WHERE user_id=? AND server_id=? ORDER BY id DESC LIMIT 1",
            (user_id, server_id),
        )
        row = await cursor.fetchone()
        warn_id = (row[0] + 1) if row else 1
        await self.connection.execute(
            "INSERT INTO warns(id, user_id, server_id, moderator_id, reason) VALUES (?, ?, ?, ?, ?)",
            (warn_id, user_id, server_id, moderator_id, reason),
        )
        await self.connection.commit()
        return warn_id

    async def remove_warn(self, warn_id: int, user_id: int, server_id: int) -> int:
        """
        Remove a warn from the database.

        :param warn_id: ID of the warn.
        :param user_id: ID of the user.
        :param server_id: ID of the server.
        :return: Remaining number of warns.
        """
        await self.connection.execute(
            "DELETE FROM warns WHERE id=? AND user_id=? AND server_id=?",
            (warn_id, user_id, server_id),
        )
        await self.connection.commit()
        cursor = await self.connection.execute(
            "SELECT COUNT(*) FROM warns WHERE user_id=? AND server_id=?",
            (user_id, server_id),
        )
        count = (await cursor.fetchone())[0]
        return count

    async def get_warnings(self, user_id: int, server_id: int) -> list:
        """
        Get all warnings of a user.

        :param user_id: ID of the user.
        :param server_id: ID of the server.
        :return: List of warnings.
        """
        cursor = await self.connection.execute(
            "SELECT user_id, server_id, moderator_id, reason, "
            "strftime('%s', created_at), id FROM warns WHERE user_id=? AND server_id=?",
            (user_id, server_id),
        )
        rows = await cursor.fetchall()
        return list(rows)
