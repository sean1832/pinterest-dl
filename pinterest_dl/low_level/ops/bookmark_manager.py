from typing import List


class BookmarkManager:
    def __init__(self, last: int) -> None:
        self.bookmarks: List[str] = []
        if last < 0 or last > 4:
            raise ValueError("Invalid last value. Must be between 0 and 4")
        self.last = last

    def add(self, bookmark: str) -> None:
        self.bookmarks.append(bookmark)

    def add_all(self, bookmarks: List[str]) -> None:
        self.bookmarks.extend(bookmarks)

    def clear(self) -> None:
        self.bookmarks.clear()

    def get(self) -> List[str]:
        if len(self.bookmarks) < self.last:
            return self.bookmarks
        return self.bookmarks[-self.last :]

    def get_all(self) -> List[str]:
        return self.bookmarks
