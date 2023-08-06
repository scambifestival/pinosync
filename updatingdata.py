import copy
import json
import os.path
import datetime
from dataclasses import dataclass
from time import sleep


import github
import requests
import yaml
from github import Github, Repository, Branch
from termcolor import colored, cprint


@dataclass
class Git:
    g: Github
    repo: Repository
    branch: Branch


@dataclass
class atrt:
    br_access_token: str
    at_creation_time: datetime.datetime
    br_refresh_token: str
    rt_creation_time: datetime.datetime
    atexp = datetime.timedelta(minutes=10)
    rtexp = datetime.timedelta(hours=168)


@dataclass
class Cred:
    git_user: str
    git_token: str
    br_token: str
    br_email: str
    br_psw: str
    ats: atrt


class dirs:
    repo = "scambi.org"
    url_r = "scambifestival/scambi.org"
    dbranch = "main"
    cbranch = "main"
    data_folder = "data/{}"  # ready to be formatted
    config_folder = ".pino/{}"  # ready to be formatted
    config_raw_url = "https://raw.githubusercontent.com/scambifestival/scambi.org/main/.pino/{}"


checking_outcome = True
cred = Cred
arrow = colored(">>> ", "light_cyan", attrs=["bold"])
igreen = colored("ⓘ  ", "green", attrs=["bold"])
ired = colored("ⓘ  ", "red", attrs=["bold"])
iyallow = colored("ⓘ  ", "yellow", attrs=["bold"])
icyan = colored("ⓘ  ", "cyan", attrs=["bold"])
dirs = dirs


# noinspection SpellCheckingInspection
def main():
    global cred
    sleep(1)
    cprint("\nPLEASE CHECK THE README FILE IN THE GITHUB REPO BEFORE USING THIS TOOL.\n", "red")
    sleep(1)
    print(icyan + "'updatingdata.py' working dirs:")
    sleep(0.4)
    print("\tRepository:\t" + dirs.repo)
    sleep(0.4)
    print("\tBranch:\t\t" + dirs.dbranch + "\n")
    sleep(0.7)
    print("----------------------------------------------------------------------------\n")
    print("Hi! This is a small tool to update JSON/CSV files in the " + dirs.url_r + " repository!")

    sleep(0.4)
    cred = credential_gatherer()

    git = github_log(user=cred.git_user, psw=cred.git_token)

    tables_infos = config_getter(git, "tablesInfos.yml", None)

    auto_update(tables_infos, config_getter(git, "toUpdate.yml", tables_infos), git)

    print("\nProcess done. Bye!")


# noinspection PyUnboundLocalVariable
def credential_gatherer():
    print("\n" + icyan + "Gathering credentials from file...")
    if os.path.isfile("gb_tokens.txt") is False:
        sleep(0.5)
        cprint("\nCredentials file not found. I need to create it.", "yellow")
        sleep(0.5)
        cprint("\n! Please note that none of those details will be shared anywhere.\n", "green")
        sleep(0.5)
        print("➔ What's your GitHub username?")
        sleep(0.2)
        user = input("\nGITHUB USERNAME " + arrow)
        while True:
            sleep(0.2)
            ans = input("\nIs '" + user + "' correct?\n\t- Press ENTER to confirm or\n\t- Type your username again\n\n"
                        + arrow)
            if ans == "":
                break
            user = ans
        sleep(0.3)
        print("\nOK!\n\n➔ What's your GitHub private access token?\nNOTE:\tIt should start with 'ghp_'.\n")
        sleep(0.2)
        git_token = input("GITHUB TOKEN " + arrow)
        sleep(0.3)
        print("\nOK!\n\n➔ What's your Pino access token?\n\t- Send 'help' to see how to create a Pino token.\n")
        sleep(0.2)
        br_token = input("PINO TOKEN " + arrow)
        if br_token.lower() == "help":
            sleep(0.2)
            print("\nThose are the steps to create a Pino Token:\n")
            sleep(0.2)
            print("\t1. Login to pino.scambi.org")
            sleep(0.2)
            print("\t2. Click on your name at the top left of the web page")
            sleep(0.2)
            print("\t3. Go to 'Token API' section")
            sleep(0.2)
            print("\t4. Click 'Create token +'; choose a name and select 'ScambiFestival' as Group")
            sleep(0.2)
            print("\t5. Be sure to give all the permissions to your private token!")
            sleep(0.2)
            br_token = input("\n➔ What's your Pino access token?\nPINO TOKEN " + arrow)
        sleep(0.3)
        print("\nOK!\n\n➔ Now I need your Pino email with which you log inside our database.")
        cprint("This info is needed for Backend API requests.\n", "green")
        sleep(0.2)
        br_email = input("PINO EMAIL " + arrow)
        while True:
            if "@" not in br_email or "." not in br_email:
                sleep(0.2)
                print("\nPlease insert a valid email.")
                br_email = input(arrow)
                continue
            sleep(0.2)
            ans = input("\nIs '" + br_email + "' correct?\n\t- Press ENTER to confirm or\n\t- Type your email again\n\n"
                        + arrow)
            if ans == "":
                break
            br_email = ans
        sleep(0.3)
        print("\nOK!\n\n➔ Last thing is your Pino password.")
        cprint("This info is needed for Backend API requests.\n", "green")
        sleep(0.2)
        br_psw = input("PINO PASSWORD " + arrow)
        while True:
            sleep(0.2)
            ans = input(
                "\nIs '" + br_psw + "' correct?\n\t- Press ENTER to confirm or\n\t- Type your password again\n"
                + arrow)
            if ans == "":
                break
            br_psw = ans

        file = open("gb_tokens.txt", "w")
        file.write("git_user " + user + "\ngit_token " + git_token + "\npino_token " + br_token + "\npino_email " +
                   br_email + "\npino_psw " + br_psw)
        file.close()
        print("\n➔ File created!")
    else:
        file = open("gb_tokens.txt", "r")
        lines = file.readlines()
        if len(lines) < 5:
            s = set()
            t = ("git_user", "git_token", "pino_token", "pino_email", "pino_psw")
            for line in lines:
                s.add(line.split(" ")[0])
            for el in t:
                if el not in s:
                    print()
                    cprint("! '" + el + "' missing in 'gb_tokens.txt' file.", "red")
            cprint("Please add missing details or delete 'gb_tokens.txt' file to be guided through the process.",
                   "red")
            exit(-3)
        for line in lines:
            if len(line.split(" ")) != 2:
                cprint("CRITICAL ERROR: 'gb_tokens.txt' WRONG FORMATTED (LINE N." + str(lines.index(line) + 1) + ").\n"
                       "Please correct the file in the script directory.", "red")
                exit(-3)
        for line in lines:
            if line.startswith("git_user"):
                user = line.split(" ")[1]
            elif line.startswith("git_token"):
                git_token = line.split(" ")[1]
            elif line.startswith("pino_token"):
                br_token = line.split(" ")[1]
            elif line.startswith("pino_email"):
                br_email = line.split(" ")[1]
            elif line.startswith("pino_psw"):
                br_psw = line.split(" ")[1]
            else:
                cprint("! Unknown line '" + line.removesuffix("\n") + "' in 'gb_tokens.txt' file.", "yellow")

    user = user.removesuffix("\n")
    git_token = git_token.removesuffix("\n")
    br_token = br_token.removesuffix("\n")
    br_email = br_email.removesuffix("\n")
    br_psw = br_psw.removesuffix("\n")

    g = Github(user, git_token)
    try:
        # noinspection PyUnusedLocal
        b = g.get_user().get_repos().totalCount
    except github.GithubException:
        cprint("\nCRITICAL ERROR: GITHUB TOKEN IS NOT CORRECT.\nPlease correct 'gb_tokens.txt' file in "
               "the script directory.\n", "red")
        exit(-1)

    res = requests.get(url="https://pino.scambi.org/api/database/fields/table/323/",
                       headers={"Authorization": "Token " + br_token})
    if res.status_code != 200:
        cprint("\nCRITICAL ERROR: BASEROW MAY NOT BE CORRECT.\nPlease check 'gb_tokens.txt' file in "
               "the script directory.\n", "red")
        exit(-2)

    res = requests.post(url="https://pino.scambi.org/api/user/token-auth/", data={"email": br_email,
                                                                                  "password": br_psw})
    if res.status_code != 200:
        if res.status_code == 401 and json.loads(res.content.decode("utf-8"))["error"] == "ERROR_INVALID_CREDENTIALS":
            cprint("Wrong Pino email or password! Please check it in the 'gb_tokens.txt' file.", "red")
            exit(-4)
        if res.status_code == 400 and "Enter a valid email address." in res.content.decode("utf-8"):
            cprint("Baserow backend API didn't like your email. Please check it in the 'gb_tokens.txt' file.", "red")
            exit(-4)
        else:
            cprint("UNKNOWN ERROR occurred trying to check Pino credentials (CODE: " + str(res.status_code) + " - " +
                   res.reason + ")\nCheck the 'gb_tokens.txt' file.", "red")
            exit(-5)

    br_access_token = json.loads(res.content.decode("utf-8"))["access_token"]
    atc = datetime.datetime.now()
    br_refresh_token = json.loads(res.content.decode("utf-8"))["refresh_token"]
    rtc = datetime.datetime.now()

    return Cred(git_user=user, git_token=git_token, br_token=br_token, br_email=br_email, br_psw=br_psw,
                ats=atrt(
                    br_access_token=br_access_token,
                    br_refresh_token=br_refresh_token,
                    at_creation_time=atc,
                    rt_creation_time=rtc
                    )
                )


def github_log(user: str, psw: str):
    g = Github(user, psw)
    repo = g.get_repo(dirs.url_r)
    git = Git(
        g=g,
        repo=repo,
        branch=repo.get_branch(dirs.dbranch)
    )
    return git


def config_getter(git: Git, config_file: str, tables_infos: dict | None):
    sleep(0.5)
    print("\n" + icyan + "Gathering '" + config_file + "' file...")
    try:
        r = git.repo.get_contents(dirs.config_folder.format(config_file), ref=dirs.cbranch)
    except github.GithubException as e:
        cprint("ERROR: GitHub API returned an error while requesting for '" + config_file + "'"".\nError Code: " +
               str(e.status), "yellow")
        sleep(1)
        print("\nA good engineer should always have a plan B... so let me try another way...\n")

        s = requests.get(dirs.config_raw_url.format(config_file))

        if not s.ok:
            cprint("ERROR: '" + config_file + "' request returned an error.\nError Code: " + str(s.status_code) +
                   "\nReason: " + s.reason, "red")
            sleep(0.3)
            print("\n" + ired + "I cannot work without the '" + config_file + "' configuration file. "
                                                                              "Fix the issue first.")
            exit(-1)
        s = s.text
    else:
        s = r.decoded_content.decode("utf-8")
    try:
        y = yaml.load(s, Loader=yaml.Loader)['tables']
    except KeyError as e:
        cprint("ERROR: 'tables' entry missing in '" + config_file + "' file. Check the file.\n"
               + str(e.__cause__), "red")
        exit(-1)

    config_checker(y, config_file, tables_infos)

    sleep(0.4)
    print(igreen + "'" + config_file + "' correctly loaded.")

    return y


def auto_update(tables_infos: dict, toUpdate: dict, git: Git):
    global checking_outcome
    d = copy.deepcopy(toUpdate)
    while True:
        if checking_outcome:
            print("\n---------------------------------------------------------------")
            sleep(0.5)
            print("Those files will be processed:\n")
            count = 1
            formats = copy.deepcopy(d)
            for item in d:
                sleep(0.2)
                file, ft, ftc = d[item]["file"], d[item]["format"], colored(d[item]["format"].upper(), "yellow")
                if file == "" or file == " ":
                    text = "\t" + str(count) + ". '" + item + "." + ft.lower() + "'"
                    while len(text) < 19:
                        text += " "
                    text += "\t(should be created in " + ftc + " format using table w/ reference name '" + \
                            item + "')"
                else:
                    text = "\t" + str(count) + ". '" + file + "'"
                    while len(text) < 19:
                        text += " "
                    text += "\t(should be updated in " + ftc + " format using" \
                                                               " table w/ reference name '" + item + "')"
                print(text)
                count += 1

            sleep(0.5)
        while True:
            if checking_outcome:
                print("\nChoose an option:")
                print("\t(Y) Proceed with processing those files.")
                print("\t(N) End the script.")
                sleep(0.3)
                print("\nOther options:")
                print("\t(U) Refresh 'toUpdate.yml' content.")
                print("\t(I) Refresh 'tablesInfos.yml' content.")
                print("\t(C) Change output file(s) format.")
                print("\t(S) Select which file(s) you want to update/create.")
                print("\t(E) Edit 'toUpdate.yml' file.")
                print("\t(T) Edit 'tablesInfos.yml' file.\n")
                sleep(0.3)
                uinput = input("(Y/N/U/I/C/S/E/T) " + arrow).lower()
                if uinput != "y" and uinput != "n" and uinput != "c" and uinput != "s" and uinput != "e" \
                        and uinput != "t" and uinput != "u" and uinput != "i":
                    print("\nDidn't understand the answer...")
                    continue
                break
            else:
                sleep(0.4)
                cprint("\n! Auto Update not available (fix configuration files first, then refresh their content "
                       "if needed)", "yellow")
                sleep(1)
                print("\nChoose an option:")
                print("\t(U) Refresh 'toUpdate.yml' content.")
                print("\t(I) Refresh 'tablesInfos.yml' content.'")
                print("\t(E) Edit 'toUpdate.yml' file.")
                print("\t(T) Edit 'tablesInfos.yml' file.")
                print("\t(N) End the script.\n")
                sleep(0.3)
                uinput = input("(U/I/E/T/N) " + arrow).lower()
                if uinput != "i" and uinput != "e" and uinput != "t" and uinput != "u" and uinput != "n":
                    print("\nDidn't understand the answer...")
                    continue
                break

        if uinput == "n":
            return

        if uinput == "c":
            # PyunboundLocalVariable: uinput non può essere 'c' se checking_outcome è False
            # noinspection PyUnboundLocalVariable
            d = formats_changer(d, formats)
            continue

        if uinput == "s":
            d = selector(d, toUpdate)
            continue

        if uinput == "e":
            o = toUpdate_editor(toUpdate, tables_infos, git)
            if o is not None:
                sleep(0.4)
                print("\n" + igreen + "Updating script 'toUpdate.yml' data...")
                sleep(1)
                toUpdate_copy = config_getter(git, "toUpdate.yml", tables_infos)
                if o == "+":
                    for el in toUpdate_copy:
                        if el not in toUpdate:
                            toUpdate[el] = toUpdate_copy[el]
                            d[el] = copy.deepcopy(toUpdate[el])
                else:
                    t = copy.deepcopy(toUpdate)
                    for el in t:
                        if el not in toUpdate_copy:
                            del toUpdate[el]
                            if el in d:
                                del d[el]
            continue

        if uinput == "t":
            c = copy.deepcopy(tables_infos)
            tables_infos = tablesInfos_editor(toUpdate, tables_infos, git)
            if tables_infos != c:
                toUpdate = config_getter(git, "toUpdate.yml", tables_infos)
                e = copy.deepcopy(d)
                for el in e:
                    if el not in toUpdate:
                        del d[el]

        if uinput == "y":
            for el in toUpdate:
                if el in formats and formats[el]["format"] != toUpdate[el]["format"]:
                    dispatcher(tables_infos, d, formats, git)
                    return
            dispatcher(tables_infos, d, None, git)
            return

        if uinput == "u":
            print("\n" + icyan + "Refreshing 'toUpdate.yml' configuration...")
            toUpdate = config_getter(git, "toUpdate.yml", tables_infos)
            continue

        if uinput == "i":
            print("\n" + icyan + "Refreshing 'tablesInfos.yml' configuration...")
            tables_infos = config_getter(git, "tablesInfos.yml", tables_infos)
            continue


def formats_changer(d: dict, formats: dict):
    print()
    count = 1
    indexes = ["{}".format(el) for el in d]
    for item in d:
        sleep(0.2)
        file, ft = d[item]["file"], d[item]["format"]
        if file == "" or file == " ":
            text = "\t" + str(count) + ". '" + item + "." + ft.lower() + "'"
        else:
            text = "\t" + str(count) + ". '" + file + "'"
        while len(text) < 18:
            text += " "
        print(text + "\t➔ Output format:\t" + ft.upper() + "\t(" + item + ")")
        count += 1
    sleep(0.5)
    while True:
        print("\nSend a list of space-separated numbers.")
        sleep(0.5)
        print("You can also:")
        sleep(0.5)
        print("\t- Send (B) to go back to the main section.\n")
        li = input(arrow).split(" ")
        while " " in li:
            li.remove(" ")
        while "" in li:
            li.remove("")
        if len(li) == 1 and not li[0].isnumeric() and li[0].lower() != "b":
            print("\nDidn't understand your input...")
            sleep(0.3)
        else:
            break

    if li[0].lower() == "b":
        return d

    for el in li:
        i = li.index(el)
        while (not el.isnumeric() and el.lower() != "b") or (el.isnumeric() and len(d) < int(el)):
            if el.isnumeric() and len(d) < int(el):
                cprint("\n! Number '" + el + "' was not in the list.\n", "yellow")
                sleep(0.5)
                print("Please type a number in the list.")
            else:
                cprint("\n! '" + el + "' has something wrong.\n", "yellow")
                sleep(0.5)
                print("Please type it again without any other char.")
            sleep(0.5)
            print("Other options:\n\t- Send '0' to ignore this number.\n\t- Send (B) to go back to the main section.")
            el = input(arrow)

        if el.lower() == "b":
            return d
        if int(el) == 0:
            li[i] = str(0)
            continue
        li[i] = el

    while str(0) in li:
        li.remove(str(0))

    print("\nApplied changes:")
    for el in d:
        i = indexes.index(el)
        if str(i + 1) in li:
            sleep(0.3)
            if formats[el]["format"].lower() == "csv":
                formats[el]["format"] = "JSON"
                print("\t➔ '" + el + "'\tCSV ➔ JSON")
            else:
                formats[el]["format"] = "CSV"
                print("\t➔ '" + el + "'\tJSON ➔ CSV")
    sleep(0.5)
    while True:
        print("\nConfirm changes?\n(Y) Yes.\n(N) No.\n")
        uin = input("(Y/N) " + arrow).lower()
        if uin != "y" and uin != "n":
            print("\nDidn't understand your input...")
        else:
            break

    if uin == "y":
        return formats
    return d


def selector(d: dict, toUpdate: dict):
    count = 1
    print("\nHere is an ordered list of files:\n")
    for el in d:
        sleep(0.2)
        if d[el]["file"].replace(" ", "") == "":
            text = "\t" + str(count) + ". '" + el + "." + d[el]["format"].lower() + "'"
            while len(text) < 18:
                text += " "
            print(text + "\t➔ C")
        else:
            text = "\t" + str(count) + ". '" + d[el]["file"] + "'"
            while len(text) < 18:
                text += " "
            print(text + "\t➔ U (" + d[el]["format"].upper() + ")")
        count += 1

    indexes = ["{}".format(el) for el in d]

    while True:
        print("\nSend a list of space-separated numbers.")
        sleep(0.5)
        print("You can also:")
        sleep(0.5)
        print("\t- Send (B) to go back to the main section.")
        sleep(0.5)
        print("\t- Send (A) to select all the files from 'toUpdate.yml' file.")
        sleep(0.5)
        print("\n" + iyallow + "You'll be able to change formats after the selection.\n")
        li = input(arrow).split(" ")
        while " " in li:
            li.remove(" ")
        while "" in li:
            li.remove("")
        if len(li) == 1 and not li[0].isnumeric() and li[0].lower() != "b" and li[0].lower() != "a":
            print("\nDidn't understand your input...")
            sleep(0.3)
        else:
            break

    if li[0].lower() == "b":
        return d

    if li[0].lower() == "a":
        return toUpdate

    for el in li:
        i = li.index(el)
        while (not el.isnumeric() and el.lower() != "b") or (el.isnumeric() and len(d) < int(el)):
            if el.isnumeric() and len(d) < int(el):
                cprint("\n! Number '" + el + "' was not in the list.\n", "yellow")
                sleep(0.5)
                print("Please type a number in the list.")
            else:
                cprint("\n! '" + el + "' has something wrong.\n", "yellow")
                sleep(0.5)
                print("Please type it again without any other char.")
            sleep(0.5)
            print("Other options:\n\t- Send '0' to ignore this number.\n\t- Send (B) to go back to the main section.\n")
            el = input(arrow)

        if el.lower() == "b":
            return d
        if int(el) == 0:
            li[i] = str(0)
            continue
        li[i] = el

    while str(0) in li:
        li.remove(str(0))

    if len(li) == 0:
        print("\nNo files selected.")
        return d

    e = copy.deepcopy(d)
    for el in d:
        i = indexes.index(el)
        if str(i + 1) not in li:
            del e[el]

    return e


def toUpdate_editor(toUpdate: dict, tables_infos: dict, git: Git):
    print("\nHere's the 'toUpdate.yml' configuration:\n")
    for el in toUpdate:
        if len(el) < 11:
            e = el + "\t"
        else:
            e = el
        sleep(0.2)
        if toUpdate[el]["file"].replace(" ", "") == "":
            n = colored("-----None-----", "yellow")
            print("\tKey: " + e + "\t➔\tOld File: " + n + "\tNew File Format: " + toUpdate[el]["format"])
        else:
            print("\tKey: " + e + "\t➔\tOld File: '" + toUpdate[el]["file"] + "'\tNew File Format: " +
                  toUpdate[el]["format"])

    print("\nSelect a key to edit its configuration.")
    sleep(0.3)
    print("Other options:")
    sleep(0.3)
    print("\t- Send (+) to add a key (and its config.) to the file.")
    sleep(0.3)
    print("\t- Send (-) to remove a key (and its config.) from the file.")
    sleep(0.3)
    print("\t- Send (B) to go back without edit the file.\n")
    sleep(0.3)

    while True:
        uin = input(arrow)

        if len(uin) == 1 and uin != "+" and uin != "-" and uin.lower() != "b":
            print("\nDidn't understand your input...")
            continue

        if len(uin) != 1 and uin not in toUpdate:
            print("\nSelected key '" + uin + "' is not in 'toUpdate.yml'.")
            continue
        break

    if uin.lower() == "b":
        return None

    if uin == "+":
        add = {}
        parameter = "key"
        while parameter:
            parameter = toUpdate_parameter_getter(add, parameter, tables_infos, toUpdate)
            if parameter is None:
                flag = 0
                for el in tables_infos:
                    if el not in toUpdate:
                        flag = 1
                        break
                if not flag:
                    return None
                return toUpdate_editor(toUpdate, tables_infos, git)
        d = copy.deepcopy(toUpdate)
        d[add["key"]] = {}
        d[add["key"]]["file"] = add["file"]
        d[add["key"]]["format"] = add["format"]
        toUpdate_updater(d, git, from_editor=True)
        return "+"

    if uin == "-":
        sleep(0.3)
        while True:
            print("\nType the key you want to remove from the configuration file."
                  "\n- Send (B) to go back without changes.\n")
            uin = input(arrow)
            if uin.lower() != "b" and uin not in toUpdate:
                sleep(0.3)
                cprint("\nSelected key '" + uin + "' is not in 'toUpdate.yml'", "yellow")
                sleep(0.3)
                continue
            break

        if uin.lower() == "b":
            return toUpdate_editor(toUpdate, tables_infos, git)

        sleep(0.4)
        print("\nSelected key:\t'" + uin + "'")
        while True:
            sleep(0.3)
            print("\nProceed?\n\t(Y) Yes.\n\t(N) No.\n")
            u = input(arrow).lower()
            if u != "y" and u != "n":
                sleep(0.3)
                print("\nDidn't understand your input...")
            break

        if u == "y":
            d = copy.deepcopy(toUpdate)
            del d[uin]
            toUpdate_updater(d, git, True)
        return "-"


def toUpdate_parameter_getter(add: dict, parameter: str, tables_infos: dict, toUpdate: dict):
    if parameter == "key":
        add[parameter] = key_selector(tables_infos, toUpdate)
        if add[parameter] is not None:
            return "file"
        return None
    if parameter == "file":
        add[parameter] = file_selector(add)
        if add[parameter] is not None:
            return "format"
        return "key"
    if parameter == "format":
        add[parameter] = format_selector(add)
        if add[parameter] is not None:
            return False  # devo usare False per terminare il ciclo
        return "file"


def key_selector(tables_infos: dict, toUpdate: dict):
    count = 0
    print("\n" + icyan + " KEY SELECTION\n")
    for el in tables_infos:
        if el not in toUpdate:
            if tables_infos[el]["view_id"] == 0:
                view_id = "0\t(Not Specified)"
            else:
                view_id = str(tables_infos[el]["view_id"])
            sleep(0.2)
            print("\tKEY: " + el)
            sleep(0.1)
            print("\t\t➔ Table name:\t\t" + tables_infos[el]["name"])
            sleep(0.1)
            print("\t\t➔ Table ID:\t\t" + str(tables_infos[el]["id"]))
            sleep(0.1)
            print("\t\t➔ View ID:\t\t" + view_id)
            sleep(0.1)
            print("\t\t➔ Included columns:\t" + tables_infos[el]["included"])
            sleep(0.1)
            if tables_infos[el]["filters"].replace(" ", "") == "":
                print("\t\t➔ Filters:\t\tNo additional filters applied.")
            else:
                count = 1
                print("\t\t➔ Filters:\t\tAddiotional Filters:")
                for el1 in tables_infos[el]["filters"].split(","):
                    el1.replace(" ", "")
                    print("\t\t\t\t\t\t" + str(count) + ". " + el1)
                    count += 1
            print()
            count += 1
    if count == 0:
        print("\n" + iyallow + "All available tables had been added to 'toUpdate.yml'.")
        sleep(0.3)
        print("First, add your tables on 'tablesInfos.yml' using (T) funcion on the main menu, than you'll be able to "
              "add them to 'toUpdate.yml'")
        return None
    sleep(0.5)
    while True:
        # KEY CHOOSING
        print("\nChoose a key to add from the list above.\n\t- Send (B) to go back without edit anything.\n")
        uin = input(arrow)
        if uin.lower() == "b":
            return None

        elif len(uin) == 1 and uin.lower() != "b":
            sleep(0.3)
            print("\nDidn't understand your input...")
            continue

        elif uin not in tables_infos:
            sleep(0.3)
            cprint("\nSelected key '" + uin + "' is not in 'tablesInfos.yml'", "yellow")
            continue

        return uin


def file_selector(add: dict):
    print("\n" + icyan + " FILE SELECTION")
    sleep(0.5)
    while True:
        print("\n\tSelected key ➔ '" + add["key"] + "'")
        sleep(0.3)
        print("\n\tType the file name in the repo that needs to be updated "
              "(send an empty string if the file needs to be created).\n\t\t- Send (B) to go back.\n")
        uin = input(arrow + "File Name: ")
        if uin.lower() == "b":
            return None

        elif len(uin) == 1 and uin.lower() != "b":
            sleep(0.3)
            print("\nDidn't understand your input...")
            continue

        elif uin != "" and len(uin.split(".")) != 2:
            sleep(0.3)
            print("\nFile extension not specified. Please include it in the file name.")
            continue

        elif uin != "" and uin.split(".")[1].lower() != "csv" and uin.split(".")[1].lower() != "json":
            sleep(0.3)
            print("\nScript only supports CSV and JSON format.")
            continue
        break

    while True:
        sleep(0.3)
        if uin != "":
            print("\nSelected file ➔ '" + uin + "'")
        else:
            print("\nSelected file ➔ '' (New File)")
        sleep(0.3)
        print("\nConfirm?\n\t(Y) Yes.\n\t(N) No\n")
        c = input("(Y/N) " + arrow).lower()
        if c != "y" and c != "n":
            print("\nDidn't understand the input...")
            continue
        break
    if c == "y":
        return uin
    return None


def format_selector(add: dict):
    print("\n" + icyan + " FORMAT SELECTION")
    sleep(0.3)
    print("\n\tSelected Key ➔\t'" + add["key"] + "'")
    sleep(0.3)
    print("\tSelected File ➔\t'" + add["file"] + "'")
    sleep(0.4)
    while True:
        print("\n\tChoose a format by selecting a number:\n\t\t1. CSV\n\t\t2. JSON\n\n\tSend (B) to go back.\n")
        uin = input("(1/2/B) " + arrow)
        if uin != "1" and uin != "2" and uin.lower() != "b":
            sleep(0.3)
            print("\nDidn't understand your input...")
            continue
        break
    if uin.lower() == "b":
        return None
    if uin == "1":
        return "CSV"
    return "JSON"


def tablesInfos_editor(toUpdate: dict, tables_infos: dict, git: Git):
    uin = ""
    c = False
    print("\nHere's the 'tablesInfos.yml' configuration.\n")
    for el in tables_infos:
        sleep(0.2)
        print("➔ " + el)
        for el1 in tables_infos[el]:
            if str(tables_infos[el][el1]).replace(" ", "") != "":
                p = str(tables_infos[el][el1])
            else:
                p = "\'\'"
            sleep(0.1)
            if el1 == "included" or el1 == "excluded":
                print("\t" + el1 + "➔\t" + p)
            else:
                print("\t" + el1 + "\t➔\t" + p)
        print()
    print("\n" + icyan + "Keys are not indented.\n")

    while uin != "b":
        print("Choose an option:")
        sleep(0.3)
        print("\t(+) ➔ Add a new table to the config.")
        sleep(0.3)
        print("\t(-) ➔ Remove a table from the config. " + colored("\t! Changes will affect 'toUpdate.yml' file.",
                                                                   "yellow"))
        sleep(0.3)
        print("\t(E) ➔ Edit an existing table.")
        sleep(0.3)
        print("\t(B) ➔ Go back without editing.\n")
        uin = input("(+/-/E/B) " + arrow).lower()
        if uin != "+" and uin != "-" and uin != "e" and uin != "b":
            print("\nDidn't understand your input...")
            continue
        break
    if uin.lower() == "b":
        return tables_infos

    if uin == "+":
        add = {}
        parameter = "key"
        while parameter:
            parameter = tablesInfos_parameter_getter(add, parameter)
            if parameter == "name" and add["key"] in tables_infos:
                sleep(1)
                print("\n" + iyallow + "Selected key '" + add["key"] + "' is already in the configuration."
                      " Further changes will affect the current table setup.\n"
                      "Follow the displayed istructions if you want to go back.")
                sleep(1)
            if parameter is None:
                return tablesInfos_editor(toUpdate, tables_infos, git)
        tables_infos[add["key"]] = {}
        for el in add:
            if el == "key":
                continue
            if add[el].isnumeric():
                tables_infos[add["key"]][el] = int(add[el])
            else:
                tables_infos[add["key"]][el] = add[el]

    elif uin == "-":
        c = True
        while True:
            print("\nChoose the key you want to remove from the list above.\n\t- Send (B) to go back.\n")
            uin = input(arrow)
            if uin.lower() == "b":
                return tablesInfos_editor(toUpdate, tables_infos, git)
            if uin not in tables_infos:
                print("\nSelected key '" + uin + "' is not in 'tablesInfos.yml'. Please select an existing key.")
                continue
            break
        print("\nSelected key ➔ '" + uin + "'\n")
        for el in tables_infos[uin]:
            if len(el) < 7:
                print("\t" + el + " ➔\t\t" + str(tables_infos[uin][el])
                      if str(tables_infos[uin][el]).replace(" ", "") != "" else "\t" + el + " ➔\t\t\'\'")
            else:
                print("\t" + el + " ➔\t" + str(tables_infos[uin][el])
                      if str(tables_infos[uin][el]).replace(" ", "") != "" else "\t" + el + " ➔\t\'\'")

        while True:
            print("\nProceed?\n\t(Y) Yes.\n\t(N) No.")
            o = input("(Y/N) " + arrow).lower()
            if o != "n" and o != "y":
                print("\nDidn't understand your input...")
                continue
            break

        if o == "y":
            del tables_infos[uin]
            if uin in toUpdate:
                del toUpdate[uin]
            t = yml_formatter(toUpdate)
        else:
            return tables_infos

    elif uin == "e":
        edit = {}
        parameter = "name"
        while True:
            print("\nChoose a key from the list above.\n\t- Send (B) to go back.\n")
            uin = input(arrow)
            if uin.lower() == "b":
                return tablesInfos_editor(toUpdate, tables_infos, git)
            if uin not in tables_infos:
                print("\nSelected key '" + uin + "' is not in 'tablesInfos.yml'. Please select an existing key.")
                continue
            break
        edit["key"] = uin
        while parameter:
            parameter = tablesInfos_parameter_getter(edit, parameter)
            if parameter == "key":
                return tablesInfos_editor(toUpdate, tables_infos, git)
        for el in tables_infos[edit["key"]]:
            tables_infos[edit["key"]][el] = edit[el]
        for el in edit:
            if el != "key" and el not in tables_infos[edit["key"]]:
                tables_infos[edit["key"]][el] = edit[el]
    s = yml_formatter(tables_infos)

    try:
        cont = git.repo.get_contents(dirs.config_folder.format("tablesInfos.yml"), ref=dirs.cbranch)
        git.repo.update_file(dirs.config_folder.format("tablesInfos.yml"), "Script configuration update.", s,
                             cont.sha, branch=dirs.cbranch)
    except github.GithubException as e:
        cprint("ERROR: GitHub API returned an error while requesting for 'tablesInfos.yml' update.\n"
               "Error Code: " + str(e.status), "red")
    else:
        print("\n" + igreen + "'tablesInfos.yml' successfully updated!")
        if c:
            print("\n" + iyallow + "Adapting changes to 'toUpdate.yml'...")
            try:
                cont = git.repo.get_contents(dirs.config_folder.format("toUpdate.yml"), ref=dirs.cbranch)
                # noinspection PyUnboundLocalVariable
                git.repo.update_file(dirs.config_folder.format("toUpdate.yml"), "Script configuration update.", t,
                                     cont.sha, branch=dirs.cbranch)
            except github.GithubException as e:
                cprint("ERROR: GitHub API returned an error while requesting for 'toUpdate.yml' update.\n"
                       "Error Code: " + str(e.status), "red")

    return config_getter(git, "tablesInfos.yml", None)


def tablesInfos_parameter_getter(add: dict, parameter: str):
    if parameter == "key":
        print("\n➔ KEY")
        print("Type the new table name:\n\t- Send (B) to go back.\n")
        add["key"] = input(arrow + "Table key ➔ ")
        if add["key"].lower() == "b":
            return None
        return "name"
    if parameter == "name":
        print("\nKey ➔ '" + add["key"] + "'")
        sleep(0.3)
        print("\n➔ NAME")
        sleep(0.2)
        print("\nType the 'name' parameter (should be the Baserow table name):\n\t- Send (B) to go back.\n")
        add["name"] = input(arrow)
        if add["name"].lower() == "b":
            return "key"
        return "id"
    if parameter == "id":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ '" + add["name"] + "'")
        sleep(0.3)
        print("\n➔ ID")
        sleep(0.2)
        print("\nType the 'id' parameter (should be the Baserow table ID):\n\t- Send (B) to go back.")
        sleep(0.3)
        print(ired + "This parameter must exists on Pino database.\n")
        add["id"] = input(arrow)
        if add["id"].lower() == "b":
            return "name"
        if not add["id"].isnumeric() or int(add["id"]) < 0:
            cprint("\nTable ID must be a positive number.", "yellow")
            return "id"
        return "view_id"
    if parameter == "view_id":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ '" + add["name"] + "'")
        print("\t'id' ➔ " + add["id"])
        sleep(0.3)
        print("\n➔ VIEW ID")
        sleep(0.2)
        print("\nType the 'view_id' parameter (send '0' as default):\n\t- Send (B) to go back.\n")
        sleep(0.3)
        add["view_id"] = input(arrow)
        if add["view_id"].lower() == "b":
            return "id"
        if not add["view_id"].isnumeric() or int(add["view_id"]) < 0:
            cprint("\nView ID must be a positive (or null) number.", "yellow")
            return "view_id"
        return "included"
    if parameter == "included":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ '" + add["name"] + "'")
        print("\t'id' ➔ " + add["id"])
        print("\t'view_id' ➔ '" + add["view_id"] + "'")
        sleep(0.3)
        print("\n➔ INCLUDED")
        sleep(0.2)
        print("\nType a comma separated list of columns you want to be included.")
        print("Send an empty string to inlcude all columns in the selected table or view.\n\t- Send (B) to go back.\n")
        print(iyallow + "Column names are case-sensitive!\n")
        add["included"] = input(arrow)
        if add["included"].lower() == "b":
            return "view_id"
        add["included"] = add["included"].replace(" ", "")
        return "excluded"
    if parameter == "excluded":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ '" + add["name"] + "'")
        print("\t'id' ➔ " + add["id"])
        print("\t'view_id' ➔ '" + add["view_id"] + "'")
        print("\t'included' ➔ '" + add["included"] + "'")
        sleep(0.3)
        print("\n➔ EXCLUDED")
        sleep(0.2)
        print("\nType a comma separated list of columns you want to be excluded.")
        print("Send an empty string to not exclude any columns from the selected table or view.\n"
              "\t- Send (B) to go back.\n")
        print(iyallow + "Column names are case-sensitive!\n")
        add["excluded"] = input(arrow)
        if add["excluded"].lower() == "b":
            return "included"
        add["excluded"] = add["excluded"].replace(" ", "")
        return "filters"
    if parameter == "filters":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ '" + add["name"] + "'")
        print("\t'id' ➔ '" + add["id"] + "'")
        print("\t'view_id' ➔ '" + add["view_id"] + "'")
        print("\t'included' ➔ '" + add["included"] + "'")
        print("\t'excluded' ➔ '" + add["excluded"] + "'")
        sleep(0.3)
        print("\n➔ FILTERS")
        sleep(0.2)
        print("\nType a comma separated list of filters ('filter__FIELDID__FILTERTYPE=VALUE').")
        print("Send an empty string to not apply filters.\n\t- Send (B) to go back.\n")
        print(iyallow + "This script only supports one-dimensional values (not matrices or arrays)\n")
        add["filters"] = input(arrow)
        if add["filters"].lower() == "b":
            return "excluded"
        return False


def yml_formatter(d: dict):
    e = {"tables": {}}
    for el in d:
        e["tables"][el] = {}
        for el1 in d[el]:
            e["tables"][el][el1] = d[el][el1]
    return yaml.dump(e)


def dispatcher(tables_infos: dict, to_update: dict, changed_formats: dict | None, git: Git):
    new_files = {}
    new_file = None

    while True:
        print("\nDo you want to store the files locally?\n\t(Y) Yes.\n\t(N) No.")
        sleep(0.3)
        cprint("\nFiles will be created in new 'new/' folder inside the script directory. "
               "Existing files in this directory will be overwritten.\n", "yellow")
        uin = input("(Y/N) " + arrow).lower()
        if uin != "n" and uin != "y":
            print("\nDidn't understand your input...")
            continue
        if uin == "y":
            try:
                os.mkdir("new")
            except OSError:
                pass
            uin = True
        else:
            uin = False
        break

    print()
    for key in to_update:
        if new_file is not None:
            print("\nJumping to the next one...")
            sleep(1)
            # noinspection PyUnusedLocal
            new_file = None
        print("➔ Updating '" + key + "' file using its table...\n")

        if changed_formats is not None:  # if changed_formats != to_update
            # i formati sono stati cambiati
            if to_update[key]["file"] != "" and to_update[key]["file"] != " ":
                new_file_name = to_update[key]["file"].split(".")[0] + "." + changed_formats[key]["format"].lower()
            else:
                new_file_name = key + "." + changed_formats[key]["format"].lower()
        else:
            if to_update[key]["file"] != "" and to_update[key]["file"] != " ":
                new_file_name = to_update[key]["file"]
            else:
                new_file_name = key + "." + to_update[key]["format"].lower()
        new_file = relations(tables_infos[key], to_update[key]["file"], new_file_name, git, True, uin)

        if new_file is not None:
            new_files[key] = new_file
        else:
            new_files[key] = to_update[key]["file"]
    print("\n" + igreen + "All files processed")
    sleep(0.5)
    if changed_formats is not None:
        while True:
            print("\nDo you want to make the format changes permanent?\n(Y) Yes.\n(N) No.\n")
            uinput = input("(Y/N) " + arrow)
            if uinput.lower() != "y" and uinput.lower() != "n":
                print("\nDidn't understand your input...")
            else:
                break
        if uinput.lower() == "y":
            for el in new_files:
                new_files.update({el: {"file": new_files[el], "format": changed_formats[el]["format"]}})
            toUpdate_updater(new_files, git, from_editor=False)
            return
    else:
        print("\n➔ Checking 'toUpdate.yml' configuration file...")
        for el in new_files:
            if new_files[el] != to_update[el]["file"]:
                toUpdate_updater(new_files, git, from_editor=False)
                return
        sleep(0.5)
        print("\n" + igreen + "'toUpdate.yml' update not needed (file names didn't change!)")


def relations(tables_infos: dict, file_to_update: str, new_file_name: str, git: Git, commit: bool, store: bool):
    h = None
    at = token_verifier()
    url = "https://pino.scambi.org/api/database/rows/table/{}/?user_field_names=true".format(int(tables_infos["id"]))
    params = ({"include": tables_infos["included"]} if tables_infos["included"].replace(" ", "") != "" else {})
    if tables_infos["excluded"].replace(" ", "") != "":
        params["exclude"] = tables_infos["excluded"]
    key_ = new_file_name[:len(new_file_name) - 5]

    if tables_infos["filters"] != "":
        for filter_ in tables_infos["filters"].split(","):
            filter_value = filter_.split("=")
            if filter_value[1].isnumeric():
                params[filter_value[0]] = int(filter_value[1])
            else:
                params[filter_value[0]] = filter_value[1]

    a2 = requests.get(
        "https://pino.scambi.org/api/database/fields/table/{}/".format(int(tables_infos["id"])),
        headers={"Authorization": "Token " + cred.br_token}
    )
    if not a2.ok:
        cprint(
            "ERROR while requesting for table fields data (TABLE_ID #" + str(tables_infos["id"]) + ").\n\n" +
            "Error code:\n\t" + str(a2.status_code) + "\nReason:\n\t" + a2.reason +
            "\n\nHidden columns will not be excluded in output file (press CTRL-C to abort operation)", "yellow")
        l1 = None
    else:
        l2 = list()
        l1 = a2.content.decode("utf-8").removesuffix("]").removeprefix("[").split("{\"id\":")
        for el in l1:
            el = "{\"id\":" + el.removesuffix(",")
            if "\"table_id\":" + str(tables_infos["id"]) in el:
                l2.append(el)
        l1 = dict()
        for el in l2:
            if el.endswith("["):
                j = json.loads(el.removesuffix("[") + "\"\"}")
            else:
                j = json.loads(el)
            l1[str(j["id"])] = j["name"]

    # a questo punto l1 è un dizionario chiave id valore name
    # faccio un check dei nomi delle colonne nei parametri 'include' e 'exclude'

    if "include" in params:
        s = ""
        n = l1.values()
        for el in params["include"].split(","):
            if el not in n:
                for el1 in n:
                    if el.lower() == el1.lower():
                        cprint("\tIncluded column '" + el + "' didn't exist on reference table but I fixed it including"
                               " '" + el1 + "' column.", "yellow")
                        sleep(0.2)
                        cprint("\n\tPlease check 'tablesInfos.yml' in order to avoid possible critical errors.\n"
                               "\tRemember that columns names are case-sensitive.\n", "yellow")
                        s += el1 + ","
                        break
                continue
            s += el + ","
        params["include"] = s.removesuffix(",")
    if "exclude" in params:
        s = ""
        n = l1.values()
        for el in params["exclude"].split(","):
            if el not in n:
                for el1 in n:
                    if el.lower() == el1.lower():
                        cprint("\tExcluded column '" + el + "' didn't exist on reference table but I fixed it excluding"
                               " '" + el1 + "' column.", "yellow")
                        sleep(0.2)
                        cprint("\n\tPlease check 'tablesInfos.yml' in order to avoid possible critical errors.\n"
                               "\tRemember that columns names are case-sensitive.\n", "yellow")
                        s += el1 + ","
                        continue
                continue
            s += el + ","
        params["exclude"] = s.removesuffix(",")

    if tables_infos["view_id"] != 0:
        params["view_id"] = int(tables_infos["view_id"])
        if at is not None:
            while True:
                a1 = requests.get(
                    "https://pino.scambi.org/api/database/views/{}/field-options/".format(params["view_id"]),
                    headers={"Authorization": "JWT " + at})
                if a1.ok:
                    break
                cprint("ERROR while asking for hidden columns in a view (VIEW_ID #" + str(params["view_id"]) + " - " +
                       "Attempt #1).\n", "yellow")
                sleep(0.5)
                cprint("Attempt #2...\n")
                a1 = requests.get(
                    "https://pino.scambi.org/api/database/views/{}/field-options/".format(params["view_id"]),
                    headers={"Authorization": "JWT " + at}
                )
                if a1.ok:
                    cprint("Attempt #2 ➔ Success!\n", "green")
                    break
                cprint("ERROR while asking for hidden columns in a view (VIEW_ID #" + str(params["view_id"]) + " - " +
                       "Attempt #2).\n\nError code:\n\t" + str(a1.status_code) + "\nReason:\n\t" + a1.reason, "yellow")
                sleep(0.3)
                cprint("Hidden columns will not be excluded in output file (press CTRL-C to abort operation)", "red")
                break
            if a1.ok:
                l2 = json.loads(a1.content.decode("utf-8"))["field_options"]
                for el in l2:
                    l2[str(el)] = l2[el]["hidden"]
                # a questo punto, l2 è un dizionario chiave id valore hidden
                h = dict()
                for el in l1:
                    for el1 in l2:
                        if el == el1:
                            h[l1[el]] = l2[el]
        else:
            cprint("Hidden columns will not be excluded from '" + new_file_name + "'.", "yellow")
    req = requests.get(
        url=url,
        headers={"Authorization": "Token " + cred.br_token},
        params=params
    )

    if req.status_code != 200:
        cprint("\tERROR while gathering '" + tables_infos["name"] + "' table from Pino. The associated file will not "
                                                                    "be updated.\n\t" + str(req.reason), "red")
        return None

    li = req.json()["results"]

    for sub_dict in li:
        if "id" in sub_dict:
            del sub_dict['id']
        if "order" in sub_dict:
            del sub_dict['order']
        for key in sub_dict:
            if type(sub_dict[key]) is list:
                if len(sub_dict[key]) == 1:
                    if "value" in sub_dict[key][0]:
                        sub_dict[key] = sub_dict[key][0]['value']
                elif len(sub_dict[key]) > 1:
                    n = list()
                    for el in sub_dict[key]:
                        if type(el) is dict and "value" in el:
                            n.append(el["value"])
                    sub_dict[key] = n
                else:
                    sub_dict[key] = ""
            elif type(sub_dict[key]) is dict:
                if len(sub_dict[key]) != 0:
                    if "value" in sub_dict[key]:
                        sub_dict[key] = sub_dict[key]["value"]
                    else:
                        sub_dict[key] = ""

    for sub_dict in li:
        for key in sub_dict:
            if type(sub_dict[key]) is str:
                if "\n" in sub_dict[key]:
                    sub_dict[key] = text_fixer(sub_dict[key])

    for sub_dict in li:
        i = li.index(sub_dict)
        d = copy.deepcopy(sub_dict)
        for el in sub_dict:
            if h[el] and (("include" in params and el not in params["include"].split(",")) or "include" not in params):
                del d[el]
        li[i] = d

    li = sorted(li, key=sorting_key)

    if new_file_name.endswith("csv"):
        s = csv_formatter(li)
    else:
        s = json.dumps(li, indent=4, ensure_ascii=False)
    print("\t" + icyan + "New content created.\n")
    if store:
        file = open("new/{}".format(new_file_name), "w")
        if os.path.isfile("new/{}".format(new_file_name)):
            file.write(s)
            file.close()
            print("\t" + igreen + "'" + new_file_name + "' correctly stored.")
        else:
            cprint("ERROR: cannot store the file locally", "red")

    if commit:
        return update_file_to_github(git, file_to_update, new_file_name, key_, s)
    else:
        return li


def token_verifier():
    global cred
    if datetime.datetime.now() - cred.ats.at_creation_time > cred.ats.atexp:
        if datetime.datetime.now() - cred.ats.rt_creation_time > cred.ats.rtexp:
            res = requests.post(url="https://pino.scambi.org/api/user/token-auth/", data={"email": cred.br_email,
                                                                                          "password": cred.br_psw})
            if not res.ok:
                cprint("ERROR getting Pino Backend API Tokens.\n\nError code:\n\t" + str(res.status_code) +
                       "Reason:\n\t" + res.reason, "red")
                return None
            cred.ats.br_access_token = json.loads(res.content.decode("utf-8"))["access_token"]
            cred.ats.at_creation_time = datetime.datetime.now()
            cred.ats.br_refresh_token = json.loads(res.content.decode("utf-8"))["refresh_token"]
            cred.ats.rt_creation_time = datetime.datetime.now()
        else:
            res = requests.post(url="https://pino.scambi.org/api/user/token-refresh/",
                                data={"refresh_token": cred.ats.br_refresh_token})
            if not res.ok:
                cprint("ERROR refreshing Pino Backend API Token.\n\nError code:\n\t" + str(res.status_code) +
                       "Reason:\n\t" + res.reason, "red")
                return None
            cred.ats.br_access_token = json.loads(res.content.decode("utf-8"))["access_token"]
            cred.ats.at_creation_time = datetime.datetime.now()
    return cred.ats.br_access_token


def csv_formatter(li: list):
    s = ""
    for el in li[0].keys():
        s += el + ","
    s = s.removesuffix(",")
    s += "\n"
    for el in li:
        for el1 in el:
            if type(el[el1]) is str and "," in el[el1]:
                t = ""
                l = False
                for e in el[el1]:
                    if e == "\"":
                        if not l:
                            t += "“"
                            l = True
                        else:
                            t += "”"
                            l = False
                    else:
                        t += e
                s += "\"" + t + "\","
            elif type(el[el1]) is list:
                t = ""
                for e in el[el1]:
                    t = t + e + ","
                s += "\"" + t.removesuffix(",") + "\","
            else:
                s += str(el[el1]) + ","
        s = s.removesuffix(",")
        s += "\n"
    s = s.removesuffix("\n")
    return s


def text_fixer(content: str):
    words = content.split(sep=" ")
    content = ""
    for word in words:
        if "\n" in word:
            word = word.replace("\n", " ")
            word = word.replace("  ", " ")
        if content == "":
            content += word
        else:
            content += " " + word
    return content


# noinspection PyUnusedLocal,DuplicatedCode
def update_file_to_github(git: Git, old_file_name: str, new_file_name: str, key: str, file_content: str):
    if old_file_name != "":
        if new_file_name == old_file_name:
            print("\t➔ Getting old file '" + old_file_name + "' content...")
            try:
                content = git.repo.get_contents(dirs.data_folder.format(old_file_name), ref=dirs.dbranch)
            except github.UnknownObjectException as e:
                if e.status == 404:
                    cprint("\n\tWARNING: '" + old_file_name + "' not found in the repository.\n", "yellow")
                    sleep(0.6)
                    print("\t" + igreen + "Jumping to the next step...")
                    sleep(0.6)
                    # Creo il file
                    print("\t➔ Creating '" + new_file_name + "'...")
                    try:
                        content = git.repo.create_file(dirs.data_folder.format(new_file_name), "Script updating.",
                                                       file_content, branch=dirs.dbranch)
                    except github.GithubException as e:
                        cprint("\n\tERROR: GitHub API returned an error when requesting to add '" + old_file_name +
                               "' file.\n\t\tError Code: " + str(e.status), "red")
                        sleep(0.6)
                        print("\n\t" + ired + "'" + old_file_name + "' cannot be created.")
                        return None
                    else:
                        print("\n\t" + igreen + "'" + old_file_name + "' successfully created.")
                else:
                    cprint("\n\tERROR: GitHub API returned an error requesting for '" + old_file_name + "' file.\n"
                           "\t\tError Code: " + str(e.status), "red")
                    sleep(0.6)
                    print("\n\t" + ired + "'" + old_file_name + "' cannot be updated or created.")
                    return None
            else:
                # modifico il file
                print("\t➔ Updating '" + old_file_name + "' content...")
                try:
                    git.repo.update_file(dirs.data_folder.format(old_file_name), "Script updating.", file_content,
                                         content.sha, branch=dirs.dbranch)
                except github.GithubException as e:
                    cprint("\n\tERROR: GitHub API returned an error requesting for '" + old_file_name + "' update."
                           "\n\t\tError Code: " + str(e.status), "red")
                    sleep(0.6)
                    print("\n\t" + ired + "'" + old_file_name + "' cannot be updated")
                    return None
                else:
                    print("\n\t" + igreen + "'" + old_file_name + "' successfully updated.")

            name = old_file_name.split(".")[0] + (".json" if old_file_name.endswith(".csv") else ".csv")

            try:
                content = git.repo.get_contents(dirs.data_folder.format(name), ref=dirs.dbranch)
            except github.UnknownObjectException:
                pass
            except github.GithubException as e:
                print("\t" + iyallow + "ERROR while searching for '" + name + "'.\n"
                      "Why is the script searching for a file with a wrong format? "
                      "Check the README file for more info.")
            else:
                while True:
                    print("\n\t" + icyan + "'" + name + "' was found in the repo. Since this file has the same name"
                                                        " but its format it wrong, do you want to delete it?")
                    sleep(0.6)
                    print("\n\t(Y) Yes.\n\t(N) No.\n")
                    uinput = input("(Y/N) " + arrow)
                    if uinput.lower() == "n" or uinput.lower() == "y":
                        break
                    print("\nDidn't understand your input...")
                    sleep(0.5)
                if uinput.lower() == "y":
                    try:
                        git.repo.delete_file(dirs.data_folder.format(name), "Script updating.", content.sha,
                                             branch=dirs.dbranch)
                    except github.GithubException as e:
                        cprint("\n\tWARNING: GitHub API returned an error when requesting for '" + name + "' removal.\n"
                               "\t\tError Code: " + str(e.status) + "\nThis file may still be in the repo.", "yellow")
                    else:
                        print("\n\t" + igreen + "'" + name + "' successfully deleted.")
            return old_file_name
        else:
            print("\t➔ Deleting old file '" + old_file_name + "'...")
            try:
                content = git.repo.get_contents(dirs.data_folder.format(old_file_name), ref=dirs.dbranch)
                git.repo.delete_file(dirs.data_folder.format(old_file_name), "Script updating.", content.sha,
                                     branch=dirs.dbranch)
            except github.GithubException as e:
                if e.status == 404:
                    cprint("\n\tWARNING: '" + old_file_name + "' not found in the repository.", "yellow")
                    sleep(0.6)
                else:
                    cprint("\n\tWARNING: GitHub API returned an error requesting for '" + old_file_name + "' removal.\n"
                           "\t\t Error Code: " + str(e.status) + "\n\t'" + old_file_name + "' may still be in the"
                           " repo.", "yellow")
                    sleep(0.6)
                print("\n\t" + igreen + "Jumping to the next step...\n")

            print("\t➔ Creating new '" + new_file_name + "' file...")
            try:
                content = git.repo.create_file(dirs.data_folder.format(new_file_name), "Script updating.", file_content,
                                               branch=dirs.dbranch)
            except github.GithubException as e:
                if e.status == 422:
                    cprint("\n\tWARNING: GitHub API returned an error while requesting to add '" + new_file_name + "'."
                           "\n\t\t Error Code: 422 (the file was already in the repo).", "yellow")
                    sleep(0.6)
                    print("\n\t" + icyan + "'" + new_file_name + "' will be updated (not created).")
                    try:
                        content = git.repo.get_contents(dirs.data_folder.format(new_file_name), ref=dirs.dbranch)
                        git.repo.update_file(dirs.data_folder.format(new_file_name), "Script updating.", file_content,
                                             content.sha, branch=dirs.dbranch)
                    except github.GithubException as e:
                        cprint("\n\tERROR: GitHub API returned an error when requesting for '" + new_file_name + "' "
                               "update.\n\t\t Error Code: " + str(e.status), "red")
                        sleep(0.6)
                        print("\n\t" + ired + "'" + new_file_name + "' cannot be updated.")
                        return None
                    else:
                        print("\n\t" + igreen + "'" + new_file_name + "' successfully updated.")
                        return new_file_name
                else:
                    cprint("\n\tERROR: GitHub API returned an error when requesting to add '" + new_file_name +
                           "' file.\n\t\t Error Code: " + str(e.status), "red")
                    sleep(0.6)
                    print("\n\t" + ired + "'" + old_file_name + "' cannot be created.")
                    return None
            else:
                print("\n\t" + igreen + "'" + new_file_name + "' successfully created.")
                return new_file_name
    else:
        # crea il secondo
        print("\t➔ Creating '" + new_file_name + "'...")
        try:
            content = git.repo.create_file(dirs.data_folder.format(new_file_name), "Script updating.",
                                           file_content, branch=dirs.dbranch)
        except github.GithubException as e:
            if e.status == 422:
                cprint("\n\tWARNING: GitHub API returned an error while requesting to add '" + new_file_name + "'."
                       "\n\t\t Error Code: 422 (the file was already in the repo).", "yellow")
                sleep(0.6)
                print("\n\t" + icyan + "'" + new_file_name + "' will be updated (not created).")
                try:
                    content = git.repo.get_contents(dirs.data_folder.format(new_file_name), ref=dirs.dbranch)
                    git.repo.update_file(dirs.data_folder.format(new_file_name), "Script updating.", file_content,
                                         content.sha, branch=dirs.dbranch)
                except github.GithubException as e:
                    cprint("\n\tERROR: GitHub API returned an error when requesting for '" + new_file_name +
                           "' update.\n\t\t Error Code: " + str(e.status), "red")
                    sleep(0.6)
                    print("\n\t" + ired + "'" + new_file_name + "' cannot be updated.")
                    return None
                else:
                    print("\n\t" + igreen + "'" + new_file_name + "' successfully updated.")
            else:
                cprint("\nERROR:\tGitHub API returned an error when requesting to add '" + new_file_name +
                       "' file.\n\t\t Error Code: " + str(e.status), "red")
                sleep(0.6)
                print("\n\t" + ired + "'" + new_file_name + "' cannot be created.")
                return None
        else:
            print("\n\t" + igreen + "'" + new_file_name + "' successfully created.")

        name = old_file_name.split(".")[0] + (".json" if old_file_name.endswith(".csv") else ".csv")
        try:
            cont = git.repo.get_contents(dirs.data_folder.format(name), ref=dirs.dbranch)
        except github.GithubException as e:
            if e.status == 404:
                pass
            else:
                print("\t" + iyallow + "ERROR while searching for '" + name + "'.\n"
                      "Why is the script searching for a file with a wrong format? "
                      "Check the README file for more info.")
        else:
            while True:
                print("\n\t" + icyan + "'" + name + "' was found in the repo. Since this file has the same name"
                      " but its format it wrong, do you want to delete it?")
                sleep(0.6)
                print("\n\t(Y) Yes.\n\t(N) No.\n")
                uinput = input("(Y/N) " + arrow)
                if uinput.lower() == "n" or uinput.lower() == "y":
                    break
                print("\nDidn't understand your input...")
                sleep(0.5)
            if uinput.lower() == "y":
                try:
                    git.repo.delete_file(dirs.data_folder.format(name), "Script updating.", cont.sha,
                                         branch=dirs.dbranch)
                except github.GithubException as e:
                    cprint("\n\tWARNING: GitHub API returned an error when requesting for '" + name + "' removal.\n"
                           "\t\tError Code: " + str(e.status) + "\nThis file may still be in the repo.", "yellow")
                else:
                    print("\n\t" + igreen + "'" + name + "' successfully deleted.")

        return new_file_name


def sorting_key(elem):
    return elem[list(elem.keys())[0]]


def toUpdate_updater(new_updated_files: dict, git: Git, from_editor: bool):
    if not from_editor:
        req = requests.get(dirs.config_raw_url.format("toUpdate.yml"))
        if req.ok:
            yamlfile = yaml.load(req.text, Loader=yaml.Loader)['tables']
            if type(new_updated_files[list(new_updated_files)[0]]) is str:
                for el in new_updated_files:
                    yamlfile[el]["file"] = new_updated_files[el]
            else:
                for el in yamlfile:
                    if el in new_updated_files:
                        yamlfile[el] = new_updated_files[el]

            new_updated_files = yamlfile
        else:
            cprint("ERROR: the 'toUpdate.yml' request returned an error. I cannot upload it.\n Error code:\t" +
                   str(req.status_code), "red")
            return

    s = yml_formatter(new_updated_files)

    try:
        cont = git.repo.get_contents(dirs.config_folder.format("toUpdate.yml"), ref=dirs.cbranch)
    except github.GithubException as e:
        cprint("\nERROR: GitHub API returned an error requesting for 'toUpdate.yml' content. I cannot upload it.\n"
               "Error code:\t" + str(e.status), "red")
    else:
        try:
            git.repo.update_file(dirs.config_folder.format("toUpdate.yml"), "Script configuration update.", s,
                                 cont.sha, branch=dirs.cbranch)
        except github.GithubException as e:
            cprint("\nERROR: GitHub API returned an error requesting for 'toUpdate.yml' content. I cannot upload it.\n"
                   "Error code:\t" + str(e.status), "red")
        else:
            sleep(0.5)
            print("\n" + igreen + "Configuration file 'toUpdate.yml' correctly updated!")

    if from_editor:
        sleep(0.4)
        print("\n" + iyallow + "Please note that it may take some minutes for changes to be applied on GitHub servers.")


def config_checker(file: dict, config_file: str, tables_infos: dict | None):
    global checking_outcome
    flag = False
    print()
    if config_file == "toUpdate.yml":
        for el in file:
            if el not in tables_infos:
                cprint("KEY ERROR: '" + el + "'.\n'toUpdate.yml' key must be in 'tablesInfos.yml' as well."
                       " Check 'toUpdate.yml'.\n", "red")
                checking_outcome = False
                flag = True
            if "file" not in file[el]:
                cprint("ERROR: 'file' missing inside '" + el + "' entry. Check 'toUpdate.yml'.\n", "red")
                checking_outcome = False
                flag = True
            if file[el]["file"].replace(" ", "") != "" and (not file[el]["file"].endswith(".csv") and
                                                            not file[el]["file"].endswith(".json")):
                cprint("ERROR: '" + file[el]["file"] + "' incorrect extension. Check 'toUpdate.yml' (" + el + ").",
                       "red")
                checking_outcome = False
                flag = True
            if "format" not in file[el]:
                cprint("ERROR: 'format' missing inside '" + el + "' entry. Check 'toUpdate.yml'.\n", "red")
                checking_outcome = False
                flag = True
            if file[el]["format"].replace(" ", "") == "" or (file[el]["format"].upper() != "CSV" and
                                                             file[el]["format"].upper() != "JSON"):
                cprint("ERROR: '" + el + "' format field is missing ('" + file[el]["format"] + "'). " +
                       "Check 'toUpdate.yml'.\n", "red")
                checking_outcome = False
                flag = True
            if len(file[el]) > 2:
                cprint("ERROR: size of entries must be 2. An entry in 'toUpdate.yml' has more than that.\n", "red")
                checking_outcome = False
                flag = True
    else:
        for el in file:
            if "name" not in file[el]:
                cprint("ERROR: 'name' key missing in '" + el + "'. Check 'tablesInfos.yml'.", "red")
                checking_outcome = False
                flag = True
            if "id" not in file[el]:
                cprint("ERROR: 'id' key missing in '" + el + "'. Check 'tablesInfos.yml'.", "red")
                checking_outcome = False
                flag = True
            if "view_id" not in file[el]:
                cprint("ERROR: 'view_id' key missing in '" + el + "'. Check 'tablesInfos.yml'.", "red")
                checking_outcome = False
                flag = True
            if "included" not in file[el]:
                cprint("ERROR: 'included' key missing in '" + el + "'. Check 'tablesInfos.yml'.", "red")
                checking_outcome = False
                flag = True
            if "excluded" not in file[el]:
                cprint("ERROR: 'excluded' key missing in '" + el + "'. Check 'tablesInfos.yml'.", "red")
                checking_outcome = False
                flag = True
            if "filters" not in file[el]:
                cprint("ERROR: 'filters' key missing in '" + el + "'. Check 'tablesInfos.yml'.", "red")
                checking_outcome = False
                flag = True
            try:
                i = int(file[el]["id"])
            except ValueError:
                i = file[el]["id"]
                cprint("ERROR: 'id' value must be a non-null positive number ('" + i + "'). Check '" + el +
                       "' entry in 'tablesInfos.yml'.", "red")
                checking_outcome = False
                flag = True
            else:
                if i <= 0:
                    cprint("ERROR: 'id' value must be a non-null positive number ('" + str(i) + "'). Check '" + el +
                           "' entry in 'tablesInfos.yml'.", "red")
                    checking_outcome = False
                    flag = True
            try:
                i = int(file[el]["view_id"])
            except ValueError:
                i = file[el]["view_id"]
                cprint("ERROR: 'view_id' value must be a positive (or null) number ('" + i + "'). Check '" + el +
                       "' entry in 'tablesInfos.yml'.", "red")
                checking_outcome = False
                flag = True
            else:
                if i < 0:
                    cprint("ERROR: 'view_id' value must be a positive (or null) number ('" + str(i) + "'). "
                           "Check '" + el + "' entry in 'tablesInfos.yml'.", "red")
                    checking_outcome = False
                    flag = True
            if file[el]["filters"].replace(" ", "") != "":
                for f in file[el]["filters"].split(","):
                    if "filter" not in f or "field" not in f or "=" not in f or "_" not in f:
                        cprint("\nWARNING: filter '" + f + "' is wrong formatted. It will be ignored during updates."
                               "Check 'tablesInfos.yml' (" + el + ").", "yellow")
    if flag:
        print()
    return


if __name__ == "__main__":
    main()
