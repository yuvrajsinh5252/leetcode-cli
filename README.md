# LeetCode CLI

A sleek command-line tool for LeetCode - solve, test, and submit problems directly from your terminal.

![image](https://s6.gifyu.com/images/bzHeo.gif)

<!-- https://github.com/user-attachments/assets/ff2eb1ce-734e-4e7a-b09c-61d6c491854e -->

### 🚀 Quick Start

#### 1. Using pip

```bash
pip install leetcli
```

#### 2. clone the repository

```bash
git clone https://github.com/yuvrajsinh5252/leetcode-cli
```

```bash
cd leetcode-cli
python -m venv .venv
source ./.venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Available Commands

| Command        | Description               | Options                                                                                                                                                                |
| -------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `lc login`     | Login to LeetCode account | -                                                                                                                                                                      |
| `lc logout`    | Logout from LeetCode      | -                                                                                                                                                                      |
| `lc profile`   | Display LeetCode profile  | -                                                                                                                                                                      |
| `lc daily`     | Show today's challenge    | `{lang}` - Language (optional)<br>`-e/--editor` - Preferred editor<br>`-f/--full` - Show full description<br>`-s/--save` - Save to file<br>`--no-editor` - Skip editor |
| `lc list`      | List available problems   | `-d/--difficulty` - Difficulty<br>`-s/--status` - Status<br>`-t/--tag` - Tag<br>`-c/--category-slug` - Category                                                        |
| `lc show`      | Display problem details   | `{Problem Name/Number}`<br>`-c/--compact` - Compact layout                                                                                                             |
| `lc test`      | Test your solution        | `{Problem Name/Number} {FILE}`                                                                                                                                         |
| `lc submit`    | Submit your solution      | `{Problem Name/Number} {FILE}`<br>`--lang` - Language<br>`-f/--force` - Skip confirmation                                                                              |
| `lc edit`      | Edit solution in editor   | `{Problem Name/Number} {lang}`<br>`-e/--editor` - Preferred editor                                                                                                     |
| `lc solutions` | View problem solutions    | `{Problem Name/Number}`<br>`-b/--best` - Show best solutions                                                                                                           |

### Usage Examples

```bash
lc list -d easy -s attempted -t array
lc edit 1 py
lc test 1 two-sum.py
lc submit 1 two-sum.py
lc solutions two-sum --best
lc daily py -e vim
```

### 🚧 Work in Progress

#### Todo

- [ ] Add support for custom test cases
- [ ] Add solution templates
