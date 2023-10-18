# Prompt Structure and Requirements
This README is for BANKER version 5 prompt.

## Release Notes
1. Find winner / Top 2 in Top 4 hot horse
2. Add Statistic about investment contrast situation, to eliminate 0% winning chance horse
3. Compute expected CI and expected win investment if the horse want to win
4. Best version to find Banker, added expected win differential

## Dimensions
| Dimension                   | Explanation                                   | Examples    | Data Type |
| ---------                   | -----------                                   | --------    | --------- |
| Win Odds                    | Win odds for horse                            | 1/2/3/4     | int       |
| Investment contrast         | Investment % contrast for top 4 hot horse     | 1/2/3/4     | int       |
| Overbought                  | Is overbought or not                          | True/False  | bool      |
| Contrast Fail Rate          | Investment fail rate based on contrast        | True/False  | bool      |
| Expected CI                 | CI is in range or not to win, J+T > 30%       | True/False  | bool      |
| Expected Win differential   | Use Expected Win odds to compute statistic    | 1/2/3/4     | int       |


## Prompt Structure
The prompt paragraphs follow a specific structure to ensure clarity and consistency. Each prompt paragraph consists of the following main parts:

SYSTEM MESSAGE: This section describes any system requirements or special reminders related to the problem. It provides essential information that users need to be aware of before proceeding with the problem.

CONCEPTS: The Concepts section contains important domain-specific concepts relevant to the problem. It serves as a dictionary of key terms and ideas that users should understand to tackle the problem effectively.

CURRENT DATA: This section takes live input from the user and may include static data obtained from other Python files as dictionary objects. For example, it can include data such as "win odds" or "jockey." This data is crucial for solving the specific problem and should be used as a reference during problem-solving.

QUESTION: The Question section presents the specific problem or question that users need to address. It clearly states the desired outcome or solution expected from the user.