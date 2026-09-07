from dataclasses import dataclass


@dataclass
class Purchase:
    euros: int


@dataclass
class Member:
    name: str
    points: int = 0

    def award_points(self, purchase: Purchase) -> None:
        self.points += purchase.euros
