

class Color:
    HEADER = '\033[95m'
    BLUE = '\033[34m'
    BLUE_BG = '\033[44m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    DARK_WHITE = '\033[37m'
    RED = '\033[91m'
    ORANGE = '\033[33m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    STRIKETHROUGH = '\033[09m'


if __name__ == '__main__':
    print(f"{Color.GREEN}green%{Color.ENDC}")
    print(f"{Color.RED}red%{Color.ENDC}")
    print(f"{Color.ORANGE}orange%{Color.ENDC}")
    print(f"{Color.DARK_WHITE}{Color.STRIKETHROUGH}gray%{Color.ENDC}")
    print(f"{Color.BLUE}❌<ClubhouseBest>{Color.BOLD}(26.8K){Color.ENDC}")
    print(f"{Color.CYAN}\u2714<ClubhouseBest>(26.8K){Color.ENDC}")
    print("No color")