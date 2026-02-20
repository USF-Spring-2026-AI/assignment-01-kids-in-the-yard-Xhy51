# AI Assignment 01 - Kids in the Yard

# Comparison

## Which tool did you use?

I used **Anthropic Claude** to generate an alternative implementation of the family tree program.

---

## What was your prompt to the LLM?

I gave Claude the complete assignment specification, which included the description of the `Person`, `PersonFactory`, and `FamilyTree` classes, CSV files used, expected interaction with users, and grading criteria on object-oriented programming, PEP 8, and efficiency. The prompt was:

> "Implement a family tree generator using Python object-oriented programming. The program uses CSV files to read first names, last names, birth rates, marriage rates, and life expectancy. The program starts with two people born in 1950 and generates their descendants. The program also allows users to query the total number of people, people by decade, and duplicate names. The program also follows PEP 8 conventions."

The prompt was refined during the second round by asking Claude to improve the responsibility of each class and to address edge cases, e.g., missing CSV files and birth years outside expected ranges.

---

## What differences are there between your implementation and the LLM output?

Several differences are noteworthy.

**1. Tree Traversal Strategy**
Claude used a recursive depth-first search to expand the family tree, whereas my solution uses a queue-based iterative BFS approach. Both methods are correct, but the queue-based approach will not run into Python's recursion limit for large trees.

**2. Class Responsibility**
Whereas the CSV parsing logic was hard-coded within the `FamilyTree` class in Claude's solution, my solution separates the data loading logic into a dedicated `PersonFactory` class. This separation makes each class easier to test and modify independently.

**3. Partner Year of Birth**
Whereas the year of birth for partners was simply the same as the person in Claude's solution, my solution randomly offsets the year of birth by a random integer in the range of -10 to +10 years, as the assignment specification requires.

**4. First Name Selection**
Whereas Claude's solution used a flat dictionary for first name lookup, my solution uses weighted random sampling based on the frequency column in the CSV file, which produces a more realistic name distribution.

**5. Last Name File Handling**
Whereas Claude hard-coded the filename as `last_names.csv`, my solution checks for both `last_names.csv` and `last_name.csv` before raising a runtime error, making the program more robust.

---

## What changes would you make to your implementation based on the LLM suggestions?

- Centralized randomness using random.Random(seed) for reproducibility
- Added by-year query in addition to by-decade
- Improved CSV parsing to handle last_names files with or without Decade column
- Allowed two root individuals to have different last names

---

## What changes would you refuse to make?

**Switching to recursion**
I would refuse to replace the iterative BFS with recursion. For a large family tree spanning many generations, the recursive approach risks hitting Python's default recursion limit and would require either raising the limit manually or restructuring the code. The iterative queue is safer and equally readable.

**Moving CSV logic into FamilyTree**
I would refuse to move the CSV reading logic into the `FamilyTree` class. Keeping `PersonFactory` responsible for data loading and person creation is a cleaner OOP design. If the data source ever changed, only `PersonFactory` would need to be modified, leaving `FamilyTree` untouched.

**Removing weighted name sampling**
I would refuse to remove the weighted random selection for first names. Using flat random selection ignores the frequency column in the CSV entirely, meaning rare names would appear as often as common ones. This contradicts the intent of the data file and produces unrealistic output.
