class BrowserVersion:
    def __init__(self, major: int = 0, minor: int = 0, build: int = 0, patch: int = 0) -> None:
        self.Major: int = major
        self.Minor: int = minor
        self.Build: int = build
        self.Patch: int = patch

    @staticmethod
    def from_str(version: str) -> "BrowserVersion":
        segs = version.split(".")
        if len(segs) != 4:
            raise ValueError(
                "Invalid version string. Must be in the format 'major.minor.build.patch'"
            )
        return BrowserVersion(int(segs[0]), int(segs[1]), int(segs[2]), int(segs[3]))

    def __str__(self) -> str:
        return f"{self.Major}.{self.Minor}.{self.Build}.{self.Patch}"
