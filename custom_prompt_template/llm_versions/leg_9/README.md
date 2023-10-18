# Prompt Structure and Requirements
This README is for LEGS version 9 prompt.

## Release Notes
1. Predict Top 4 horses
2. Rank all horses
3. Rank based on Top 4 % statistic
4. Good result for Quartet

## Dimensions
| Dimension                   | Explanation                                   | Examples    | Data Type |
| ---------                   | -----------                                   | --------    | --------- |
| Win Odds                    | Win odds for horse                            | 1/2/3/4     | int       |
| QW CI                       | Quinella-Win CI                               | 1/2/3       | int       |
| WP CI                       | Win-Place CI                                  | 1/2/3       | int       |
| Jockey / Trainer            | Jockey Code                                   | PZ          | str       |
| Jockey / Trainer Tier       | Jockey / Trainer tier by winning chance       | 1/2/3       | int       |
| Jockey / Trainer Win Rate   | Jockey / Trainer Top 4 chance by Win Matrix   | 1/2/3       | int       |
| Speed Pro                   | Speed Pro Score (Top 4)                       | 1/2/3       | int       |
| Cold-Door                   | Cold-Door Score (Top 4)                       | 1/2/3       | int       |
| Trackwork                   | Trackwork Score (Top 4)                       | 1/2/3       | int       |
| Overbought                  | Overbought Top 4 chance                       | 1/2/3/4     | int       |
| Win Investment              | Investment difference (Top 4)                 | 1/2/3/4     | int       |


## Prompt Structure
The prompt paragraphs follow a specific structure to ensure clarity and consistency. Each prompt paragraph consists of the following main parts:

SYSTEM MESSAGE: This section describes any system requirements or special reminders related to the problem. It provides essential information that users need to be aware of before proceeding with the problem.

CONCEPTS: The Concepts section contains important domain-specific concepts relevant to the problem. It serves as a dictionary of key terms and ideas that users should understand to tackle the problem effectively.

CHAIN OF THOUGHT: This section describes the steps to solve the problems and gives appropriate answer and ranking.

CURRENT DATA: This section takes live input from the user and may include static data obtained from other Python files as dictionary objects. For example, it can include data such as "win odds" or "jockey." This data is crucial for solving the specific problem and should be used as a reference during problem-solving.

QUESTION: The Question section presents the specific problem or question that users need to address. It clearly states the desired outcome or solution expected from the user.