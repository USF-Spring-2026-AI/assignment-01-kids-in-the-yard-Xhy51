import csv
import math
import os
import random
from collections import Counter, deque


# e.g. 1983 -> "1980s"
def decade_str(year):
    return f"{(year // 10) * 10}s"


class Person:
    def __init__(self, pid, first_name, last_name, gender, year_born, year_died, is_descendant):
        self.pid = pid
        self.first_name = first_name
        self.last_name = last_name
        self.gender = gender
        self.year_born = year_born
        self.year_died = year_died
        self.is_descendant = is_descendant

        self.partner_id = None
        self.children_ids = []

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class PersonFactory:
    """Reads data files and creates Person instances."""

    def __init__(self, rng):
        # use a shared rng instance so all randomness is centralized
        self.rng = rng

        # decade -> (birth_rate, marriage_rate)
        self.birth_marriage = {}
        # (decade, gender) -> (names_list, weights_list)
        self.first_names = {}
        # year -> life expectancy float
        self.life_exp = {}
        self.rank_probs = []
        # decade -> (names_list, weights_list), normalized by rank probability
        self.last_names_by_decade = {}

        self._next_id = 1

    def read_files(self):
        self._read_birth_marriage("birth_and_marriage_rates.csv")
        self._read_first_names("first_names.csv")
        self._read_life_expectancy("life_expectancy.csv")
        self._read_rank_probs("rank_to_probability.csv")
        self._read_last_names()

    def _read_birth_marriage(self, path):
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.birth_marriage[row["decade"]] = (
                    float(row["birth_rate"]),
                    float(row["marriage_rate"])
                )

    def _read_first_names(self, path):
        # columns: decade, gender, name, frequency
        buckets = {}
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = (row["decade"], row["gender"].strip().lower())
                if key not in buckets:
                    buckets[key] = ([], [])
                buckets[key][0].append(row["name"])
                buckets[key][1].append(float(row["frequency"]))
        self.first_names = buckets

    def _read_life_expectancy(self, path):
        # columns: Year, Period life expectancy at birth
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.life_exp[int(row["Year"])] = float(row["Period life expectancy at birth"])

    def _read_rank_probs(self, path):
        # single line of 30 comma-separated probabilities
        with open(path, encoding="utf-8") as f:
            line = f.readline().strip()
        self.rank_probs = [float(x) for x in line.split(",") if x.strip()]
        if len(self.rank_probs) != 30:
            raise ValueError("rank_to_probability.csv should have exactly 30 values")

    def _read_last_names(self):
        path = None
        for candidate in ["last_names.csv", "last_name.csv"]:
            if os.path.exists(candidate):
                path = candidate
                break
        if path is None:
            raise FileNotFoundError("Could not find last_names.csv or last_name.csv")

        # defensive parsing: handle files with or without a Decade column
        # if no decade column exists, pool all names under "1950s" as fallback
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []
            has_decade = any(h.lower() == "decade" for h in headers)

            for row in reader:
                decade = "1950s"
                if has_decade:
                    decade = row.get("Decade") or row.get("decade") or "1950s"

                name = row.get("LastName") or row.get("last_name") or row.get("lastname")
                rank_str = row.get("Rank") or row.get("rank")
                if not name or not rank_str:
                    continue
                rank = int(rank_str)
                if decade not in self.last_names_by_decade:
                    self.last_names_by_decade[decade] = ([], [])
                self.last_names_by_decade[decade][0].append(name.strip())
                self.last_names_by_decade[decade][1].append(self.rank_probs[rank - 1])

        # normalize weights per decade so they sum to 1
        for decade in self.last_names_by_decade:
            names, weights = self.last_names_by_decade[decade]
            total = sum(weights)
            self.last_names_by_decade[decade] = (names, [w / total for w in weights])

    def _new_id(self):
        pid = self._next_id
        self._next_id += 1
        return pid

    def pick_gender(self):
        return "male" if self.rng.random() < 0.5 else "female"

    def pick_first_name(self, year_born, gender):
        key = (decade_str(year_born), gender)
        names, weights = self.first_names[key]
        return self.rng.choices(names, weights=weights, k=1)[0]

    def pick_last_name(self, year_born=None):
        # use the decade matching year_born; clamp to 1950s if we don't have data
        decade = decade_str(year_born) if year_born is not None else "1950s"
        if decade not in self.last_names_by_decade:
            decade = "1950s"
        names, weights = self.last_names_by_decade[decade]
        return self.rng.choices(names, weights=weights, k=1)[0]

    def compute_year_died(self, year_born):
        # clamp year_born so we don't index outside the life expectancy table
        clamped = max(min(year_born, max(self.life_exp)), min(self.life_exp))
        le = self.life_exp[clamped]
        age = int(round(le)) + self.rng.randint(-10, 10)
        return year_born + max(0, age)

    def get_person(self, year_born, is_descendant, root_last_names, forced_last=None):
        gender = self.pick_gender()
        first = self.pick_first_name(year_born, gender)

        if forced_last is not None:
            last = forced_last
        elif is_descendant:
            last = self.rng.choice(list(root_last_names))
        else:
            last = self.pick_last_name(year_born)

        return Person(
            pid=self._new_id(),
            first_name=first,
            last_name=last,
            gender=gender,
            year_born=year_born,
            year_died=self.compute_year_died(year_born),
            is_descendant=is_descendant,
        )


class FamilyTree:
    def __init__(self, seed=None):
        # centralized rng so results are reproducible when seed is set
        self.rng = random.Random(seed)
        self.factory = PersonFactory(self.rng)
        self.people = {}
        self.root_last_names = ("", "")

    def build(self):
        """Generate the full family tree starting from two people born in 1950."""
        # two root people can have different last names; descendants inherit one of the two
        root_last_1 = self.factory.pick_last_name(1950)
        root_last_2 = self.factory.pick_last_name(1950)

        p1 = self.factory.get_person(1950, is_descendant=True,
                                     root_last_names=(root_last_1, root_last_2),
                                     forced_last=root_last_1)
        p2 = self.factory.get_person(1950, is_descendant=True,
                                     root_last_names=(root_last_1, root_last_2),
                                     forced_last=root_last_2)
        p1.partner_id = p2.pid
        p2.partner_id = p1.pid

        self.people[p1.pid] = p1
        self.people[p2.pid] = p2
        self.root_last_names = (p1.last_name, p2.last_name)

        # BFS - use deque for O(1) popleft instead of O(n) pop(0)
        visited_units = set()
        queue = deque([p1.pid, p2.pid])

        while queue:
            pid = queue.popleft()
            person = self.people[pid]

            unit = self._unit_key(person)
            if unit in visited_units:
                continue
            visited_units.add(unit)

            self._maybe_add_partner(person)
            for child in self._make_children(person):
                self.people[child.pid] = child
                queue.append(child.pid)

    def _unit_key(self, person):
        if person.partner_id is None:
            return (person.pid, 0)
        return tuple(sorted([person.pid, person.partner_id]))

    def _maybe_add_partner(self, person):
        if person.partner_id is not None:
            return
        _, marriage_rate = self.factory.birth_marriage[decade_str(person.year_born)]
        if self.rng.random() >= marriage_rate:
            return

        yb = max(1950, min(2120, person.year_born + self.rng.randint(-10, 10)))
        partner = self.factory.get_person(yb, is_descendant=False,
                                          root_last_names=self.root_last_names)
        partner.partner_id = person.pid
        person.partner_id = partner.pid
        self.people[partner.pid] = partner

    def _make_children(self, person):
        parents = [person]
        if person.partner_id is not None:
            parents.append(self.people[person.partner_id])

        elder = min(parents, key=lambda p: p.year_born)
        birth_rate, _ = self.factory.birth_marriage[decade_str(elder.year_born)]

        # +/- 1.5 around birth_rate, rounded up per assignment spec
        min_kids = max(0, math.ceil(birth_rate - 1.5))
        max_kids = max(min_kids, math.ceil(birth_rate + 1.5))
        n_kids = self.rng.randint(min_kids, max_kids)

        start_year = elder.year_born + 25
        end_year = min(elder.year_born + 45, 2120)

        if start_year > 2120:
            return []

        children = []
        for _ in range(n_kids):
            yb = self.rng.randint(start_year, end_year)
            is_desc = any(p.is_descendant for p in parents)
            child = self.factory.get_person(yb, is_descendant=is_desc,
                                            root_last_names=self.root_last_names)
            for parent in parents:
                parent.children_ids.append(child.pid)
            children.append(child)

        return children

    def total_people(self):
        return len(self.people)

    def total_by_decade(self):
        counts = Counter(decade_str(p.year_born) for p in self.people.values())
        return sorted(counts.items(), key=lambda x: int(x[0][:4]))

    def total_by_year(self):
        counts = Counter(p.year_born for p in self.people.values())
        return sorted(counts.items())

    def duplicate_names(self):
        counts = Counter(p.full_name for p in self.people.values())
        return sorted([name for name, c in counts.items() if c > 1])

    def run(self):
        print("Reading files...")
        self.factory.read_files()

        print("Generating family tree...")
        self.build()

        while True:
            print("\nAre you interested in:")
            print("(T)otal number of people in the tree")
            print("Total number of people in the tree by (D)ecade")
            print("Total number of people in the tree by (Y)ear")
            print("(N)ames duplicated")
            print("(Q)uit")

            choice = input("> ").strip().lower()

            if choice == "t":
                print(f"The tree contains {self.total_people()} people total")
            elif choice == "d":
                for decade, count in self.total_by_decade():
                    print(f"{decade}: {count}")
            elif choice == "y":
                for year, count in self.total_by_year():
                    print(f"{year}: {count}")
            elif choice == "n":
                dups = self.duplicate_names()
                print(f"There are {len(dups)} duplicate names in the tree:")
                for name in dups:
                    print(f"* {name}")
            elif choice == "q":
                break
            else:
                print("Please enter T, D, Y, N, or Q.")


if __name__ == "__main__":
    tree = FamilyTree(seed=None)
    tree.run()
