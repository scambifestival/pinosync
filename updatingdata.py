import copy
import json
import os.path
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
class Cred:
    git_user: str
    git_token: str
    br_token: str


cred = Cred
arrow = colored(">>> ", "light_cyan", attrs=["bold"])
igreen = colored("ⓘ  ", "green", attrs=["bold"])
ired = colored("ⓘ  ", "red", attrs=["bold"])
iyallow = colored("ⓘ  ", "yellow", attrs=["bold"])
icyan = colored("ⓘ  ", "cyan", attrs=["bold"])


# noinspection SpellCheckingInspection
def main():
    global cred
    sleep(1)
    cprint("\nPLEASE CHECK THE README FILE IN THE GITHUB REPO BEFORE USING THIS TOOL.\n", "red")
    sleep(2)
    print("----------------------------------------------------------------------------\n")
    print("Hi! This is a small tool to update JSON/CSV files in the scambi.org/data repository!")

    cred = credential_gatherer()

    git = github_log(user=cred.git_user, psw=cred.git_token)

    tables_infos = config_getter(git, "tablesInfos.yml")

    auto_update(tables_infos, config_getter(git, "toUpdate.yml"), git)

    print("\nProcess done. Bye!")


def credential_gatherer():
    print("\n" + igreen + "Gathering credentials from file...")
    if os.path.isfile("gb_tokens.txt") is False:
        sleep(0.5)
        cprint("\nCredentials file not found. I need to create it.", "yellow")
        sleep(0.5)
        user = input("➔ What's your GitHub username?\t")
        while True:
            sleep(0.2)
            ans = input("\nIs '" + user + "' correct?\n\t- Press ENTER to confirm or\n\t- Type your username again\n"
                        + arrow)
            if ans == "":
                break
            user = ans
        sleep(0.5)
        print("\nOK!\n\n➔ What's your GitHub private access token?\nNOTE:\tIt should start with 'ghp_'.")
        sleep(0.5)
        cprint("Please note that this detail will NOT be shared.\n", "green")
        git_token = input("GITHUB TOKEN " + arrow)
        sleep(0.5)
        print("\nOK!\n\n➔ What's your Pino access token?\n\t- Send 'help' to see how to create a Pino token.")
        cprint("Please note that this detail will NOT be shared.\n", "green")
        br_token = input(arrow)
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

        file = open("gb_tokens.txt", "w")
        file.write("git_user " + user + "\ngit_token " + git_token + "\npino_token " + br_token)
        file.close()
        print("\n➔ File created!")
    else:
        file = open("gb_tokens.txt", "r")
        lines = file.readlines()
        if len(lines) != 3:
            cprint("CRITICAL ERROR: 'gb_tokens.txt' WRONG FORMATTED.\nPlease correct the file in the script directory.",
                   "red")
        for line in lines:
            if len(line.split(" ")) != 2:
                cprint("CRITICAL ERROR: 'gb_tokens.txt' WRONG FORMATTED (LINE N." + str(lines.index(line)+1) + ").\n"
                       "Please correct the file in the script directory.", "red")
                exit(-3)
        user = lines[0].split(" ")[1]
        git_token = lines[1].split(" ")[1]
        br_token = lines[2].split(" ")[1]

    user = user.removesuffix("\n")
    git_token = git_token.removesuffix("\n")
    br_token = br_token.removesuffix("\n")

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
        cprint("\nCRITICAL ERROR: BASEROW TOKEN IS NOT CORRECT.\nPlease correct 'gb_tokens.txt' file in "
               "the script directory.\n", "red")
        exit(-2)

    return Cred(git_user=user, git_token=git_token, br_token=br_token)


def github_log(user: str, psw: str):
    g = Github(user, psw)
    # repo = g.git_repo("scambifestival/scambi.org")
    repo = g.get_repo("2ale2/scambifestival-ubjs")
    git = Git(
        g=g,
        repo=repo,
        branch=repo.get_branch("master")
    )
    return git


def config_getter(git: Git, config_file: str):
    try:
        r = git.repo.get_contents("config/{}".format(config_file), ref="master")
    except github.GithubException as e:
        cprint("ERROR: GitHub API returned an error while requesting for '" + config_file + "'"".\nError Code: " +
               str(e.status), "yellow")
        sleep(1)
        print("\nA good engineer should always have a plan B... so let me try another way...\n")

        url = 'https://raw.githubusercontent.com/2ale2/scambifestival-ubjs/master/config/{}'.format(config_file)
        s = requests.get(url)

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

    return yaml.load(s, Loader=yaml.Loader)['tables']


def auto_update(tables_infos: dict, toUpdate: dict, git: Git):
    if toUpdate is not None:
        d = copy.deepcopy(toUpdate)
        while True:
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
                print("\nChoose an option:")
                print("(Y) Proceed with processing those files.")
                print("(N) End the script.")
                sleep(0.3)
                print("\nOther options:")
                print("(C) Change output file(s) format.")
                print("(S) Select which file(s) you want to update/create.")
                print("(E) Edit 'toUpdate.yml' file.")
                print("(T) Edit 'tablesInfos.yml' file.\n")
                sleep(0.3)
                uinput = input("(Y/N/C/S/E) " + arrow).lower()
                if uinput != "y" and uinput != "n" and uinput != "c" and uinput != "s" and uinput != "e" \
                        and uinput != "t":
                    print("\nDidn't understand the answer...")
                    continue
                break

            if uinput == "n":
                return

            if uinput == "c":
                d = formats_changer(d, formats)
                continue

            if uinput == "s":
                d = selector(d, toUpdate)
                continue

            if uinput == "e":
                o = toUpdate_editor(toUpdate, tables_infos, git)
                if o is not None:
                    print("\n" + igreen + "Updating script 'toUpdate.yml' data...")
                    sleep(1)
                    toUpdate_copy = config_getter(git, "toUpdate.yml")
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
                tables_infos = tablesInfos_editor(toUpdate, tables_infos, git)

            if uinput == "y":
                for el in toUpdate:
                    if el in formats and formats[el]["format"] != toUpdate[el]["format"]:
                        dispatcher(tables_infos, d, formats, git)
                        return
                dispatcher(tables_infos, d, None, git)
                return
    else:
        cprint("\nERROR: auto-update not available. Check the start warning for more infos.\n", "red")


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
        return

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
        if str(i+1) not in li:
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
        while True:
            add["key"] = key_selector(tables_infos, toUpdate)
            if add["key"] is None:
                return toUpdate_editor(toUpdate, tables_infos, git)
            add["file"] = file_selector(add)
            if add["file"] is None:
                continue
            add["format"] = format_selector(add)
            if add["format"] is None:
                add["file"] = file_selector(add)
                if add["file"] is None:
                    continue
            break
        d = copy.deepcopy(toUpdate)
        d[add["key"]] = {}
        d[add["key"]]["file"] = add["file"]
        d[add["key"]]["format"] = add["format"]
        toUpdate_updater(d, git, from_editor=True)
        return "+"

    if uin == "-":
        sleep(0.3)
        print("\nHere's the list of keys you can delete.")
        for el in toUpdate:
            sleep(0.3)
            text = "\t" + el
            while len(text) < 10:
                text += " "
            text += "\tFile ➔\t"
            if toUpdate[el]["file"].replace(" ", "") == "":
                text += "New File"
            else:
                text += toUpdate[el]["file"]
            while len(text) < 37:
                text += " "
            print(text + "\t(" + toUpdate[el]["format"] + ")")
        sleep(0.5)
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
            print("\nProceed?\n(Y) Yes.\n(N) No.\n")
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


def tablesInfos_editor(toUpdate: dict, tables_infos: dict, git: Git):
    uin = ""
    c = bool
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
            if el1 == "included":
                print("\t" + el1 + "➔\t" + p)
            else:
                print("\t" + el1 + "\t➔\t" + p)
    print("\n" + icyan + "Keys are not indented.\n")

    while uin != "b":
        print("Choose an option:")
        sleep(0.3)
        print("\t(+) ➔ Add a new table to the config.")
        sleep(0.3)
        print("\t(-) ➔ Remove a table fromt the config. " + colored("\t! Changes will affect 'toUpdate.yml' file.",
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

    if uin == "+":
        add = {}
        parameter = "key"
        while not parameter:
            parameter = tablesInfos_parameter_getter(add, parameter)
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
        while not parameter:
            parameter = tablesInfos_parameter_getter(edit, parameter)
            if parameter == "key":
                return tablesInfos_editor(toUpdate, tables_infos, git)
        for el in tables_infos[edit["key"]]:
            tables_infos[edit["key"]][el] = edit[el]

    s = yml_formatter(tables_infos)

    try:
        cont = git.repo.get_contents("config/tablesInfos.yml", ref="master")
        git.repo.update_file("config/tablesInfos.yml", "Script configuration update.", s, cont.sha, branch="master")
    except github.GithubException as e:
        cprint("ERROR: GitHub API returned an error while requesting for 'tablesInfos.yml' update.\n"
               "Error Code: " + str(e.status), "red")
    else:
        print(igreen + "'tablesInfos.yml' successfully updated!")
        if c:
            print("\n" + iyallow + "Adapting changes to 'toUpdate.yml'...")
            s = list()
            for el in toUpdate:
                s.append(el)
            s = json.dumps(s, indent=4, ensure_ascii=False)
            try:
                cont = git.repo.get_contents("config/toUpdate.yml", ref="master")
                git.repo.update_file("config/toUpdate.yml", "Script configuration update.", s, cont.sha,
                                     branch="master")
            except github.GithubException as e:
                cprint("ERROR: GitHub API returned an error while requesting for 'toUpdate.yml' update.\n"
                       "Error Code: " + str(e.status), "red")

    return config_getter(git, "tablesInfos.yml")


def tablesInfos_parameter_getter(add: dict, parameter: str):
    if parameter == "key":
        print("\nType the new table name:\n\t- Send (B) to go back.\n")
        add["key"] = input(arrow + "Table key ➔ ")
        if add["key"].lower() == "b":
            return None
        return "name"
    elif parameter == "name":
        print("\nKey ➔ '" + add["key"])
        sleep(0.3)
        print("\nType the 'name' parameter (should be the Baserow table name):\n\t- Send (B) to go back.\n")
        add["name"] = input(arrow)
        if add["name"].lower() == "b":
            return "key"
        return "id"
    if parameter == "id":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ " + add["name"] + "'")
        sleep(0.3)
        print("\nType the 'id' parameter (should be the Baserow table ID):\n\t- Send (B) to go back.")
        sleep(0.3)
        print(ired + "This parameter must exists on Pino database.\n")
        add["id"] = input(arrow)
        if add["id"].lower() == "b":
            return "name"
        if not add["id"].isnumeric():
            cprint("\nTable ID must be a number.", "yellow")
            return "id"
        return "view_id"
    if parameter == "view_id":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ " + add["name"] + "'")
        print("\t'id' ➔ " + add["id"] + "'")
        sleep(0.3)
        print("\nType the 'view_id' parameter (send '0' as default):\n\t- Send (B) to go back.\n")
        sleep(0.3)
        add["view_id"] = input(arrow)
        if add["view_id"].lower() == "b":
            return "id"
        if not add["view_id"].isnumeric():
            cprint("\nView ID must be a number.", "yellow")
            return "view_id"
        return "included"
    if parameter == "included":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ " + add["name"] + "'")
        print("\t'id' ➔ " + add["id"] + "'")
        print("\t'view_id' ➔ " + add["view_id"] + "'")
        sleep(0.3)
        print("\nType a comma separated list of columns you want to be included.\n\t- Send (B) to go back.")
        print("Send an empty string to inlcude all columns in the selected table or view.\n")
        print(iyallow + "Column names are case-sensitive!")
        add["included"] = input(arrow)
        if add["included"].lower() == "b":
            return "view_id"
        return "filters"
    if parameter == "filters":
        print("\nKey ➔ '" + add["key"] + "'")
        print("\t'name' ➔ " + add["name"] + "'")
        print("\t'id' ➔ " + add["id"] + "'")
        print("\t'view_id' ➔ " + add["view_id"] + "'")
        print("\t'included' ➔ " + add["included"] + "'")
        sleep(0.3)
        print("\nType a comma separated list of filters ('filter__FIELDID__FILTERTYPE=VALUE').\n"
              "\t- Send (B) to go back.")
        print("Send an empty string to not apply filters.\n")
        print(iyallow + "This script only supports one-dimensional values (not matrices or arrays)\n")
        add["filters"] = input(arrow)
        if add["filters"].lower() == "b":
            return "included"
        return True


def yml_formatter(d: dict):
    d["tables"] = d
    return yaml.dump(d)


def key_selector(tables_infos: dict, toUpdate: dict):
    print("\n" + icyan + " KEY SELECTION\n")
    for el in tables_infos:
        if el not in toUpdate:
            if tables_infos[el]["view_id"] == 0:
                view_id = "0\t(Not Specified)"
            else:
                view_id = str(tables_infos[el]["view_id"])
            sleep(0.4)
            print("\tKEY: " + el)
            sleep(0.2)
            print("\t\t➔ Table name:\t\t" + tables_infos[el]["name"])
            sleep(0.2)
            print("\t\t➔ Table ID:\t\t" + str(tables_infos[el]["id"]))
            sleep(0.2)
            print("\t\t➔ View ID:\t\t" + view_id)
            sleep(0.2)
            print("\t\t➔ Included columns:\t" + tables_infos[el]["included"])
            sleep(0.2)
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
            cprint("Selected key '" + uin + "' is not in 'tablesInfos.yml'", "yellow")
            continue

        return uin


def file_selector(add: dict):
    sleep(0.5)
    while True:
        print("\nSelected key ➔ '" + add["key"] + "'")
        sleep(0.3)
        print("\nType the file name in the repo that needs to be updated "
              "(send an empty string if the file needs to be created).\n\t- Send (B) to go back.\n")
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
        print("\nConfirm?\n(Y) Yes\n(N) No\n")
        c = input("(Y/N) " + arrow).lower()
        if c != "y" and c != "n":
            print("\nDidn't understand the input...")
            continue
        break
    if c == "y":
        return uin
    return file_selector(add)


def format_selector(add: dict):
    sleep(0.3)
    print("\nSelected Key ➔\t'" + add["key"] + "'")
    sleep(0.3)
    print("Selected File ➔\t'" + add["file"] + "'")
    sleep(0.4)
    while True:
        print("\nChoose a format by selecting a number:\n\t1. CSV\n\t2. JSON\n\nSend (B) to go back.\n")
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


def dispatcher(tables_infos: dict, to_update: dict, changed_formats: dict | None, git: Git):
    new_files = {}
    new_file = None

    while True:
        print("\nDo you want to store the files locally?\n\t(Y) Yes.\n\t(N) No.")
        sleep(0.3)
        cprint("\nFiles will be created in new 'new/' folder inside the script directory. "
               "Existing files in this directory will be overwritten.", "yellow")
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
            new_file = None
        print("➔ Updating '" + key + "' file using its table...\n")
        if key not in tables_infos:
            errors_handler(key)

        elif "id" not in tables_infos[key]:
            errors_handler("id")

        elif "view_id" not in tables_infos[key]:
            errors_handler("view_id")

        elif "included" not in tables_infos[key]:
            errors_handler("included")

        elif "filters" not in tables_infos[key]:
            errors_handler("filters")

        else:
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
    url = "https://pino.scambi.org/api/database/rows/table/{}/?user_field_names=true".format(tables_infos["id"])
    params = {"include": tables_infos["included"]}
    key_ = new_file_name[:len(new_file_name) - 5]

    if tables_infos["filters"] != "":
        for filter_ in tables_infos["filters"].split(","):
            filter_value = filter_.split("=")
            if filter_value[1].isnumeric():
                params[filter_value[0]] = int(filter_value[1])
            else:
                params[filter_value[0]] = filter_value[1]

    if tables_infos["view_id"] != 0:
        params["view_id"] = int(tables_infos["view_id"])

    req = requests.get(
        url=url,
        headers={"Authorization": "Token " + cred.br_token},
        params=params
    )

    if req.status_code != 200:
        cprint("\tERROR while gathering '" + tables_infos["name"] + "' table from Pino. The associated file will not "
                                                                    "be updated.\n\t" + str(req.headers), "red")
        return None

    li = req.json()["results"]

    for sub_dict in li:
        if "id" in sub_dict:
            del sub_dict['id']
        if "order" in sub_dict:
            del sub_dict['order']
        for key in sub_dict:
            if type(sub_dict[key]) is list:
                if len(sub_dict[key]) != 0:
                    if "value" in sub_dict[key][0]:
                        sub_dict[key] = sub_dict[key][0]['value']
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


def csv_formatter(li: list):
    s = ""
    for el in li[0].keys():
        s += el + ","
    s = s.removesuffix(",")
    s += "\n"
    for el in li:
        for el1 in el:
            if type(el[el1]) is str and "," in el[el1]:
                s += "\"" + el[el1] + "\","
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
                content = git.repo.get_contents("data/{}".format(old_file_name), ref="master")
            except github.UnknownObjectException as e:
                if e.status == 404:
                    cprint("\n\tWARNING: '" + old_file_name + "' not found in the repository.\n", "yellow")
                    sleep(0.6)
                    print("\t" + igreen + "Jumping to the next step...")
                    sleep(0.6)
                    # Creo il file
                    print("\t➔ Creating '" + new_file_name + "'...")
                    try:
                        content = git.repo.create_file("data/{}".format(new_file_name), "Script updating.",
                                                       file_content, branch="master")
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
                    git.repo.update_file("data/{}".format(old_file_name), "Script updating.", file_content, content.sha,
                                         branch="master")
                except github.GithubException as e:
                    cprint("\n\tERROR: GitHub API returned an error requesting for '" + old_file_name + "' update."
                           "\n\t\tError Code: " + str(e.status), "red")
                    sleep(0.6)
                    print("\n\t" + ired + "'" + old_file_name + "' cannot be updated")
                    return None
                else:
                    print("\n\t" + igreen + "'" + old_file_name + "' successfully updated.")

            if old_file_name.endswith(".csv"):
                name = old_file_name.split(".")[0] + ".json"
            else:
                name = old_file_name.split(".")[0] + ".csv"

            try:
                content = git.repo.get_contents("data/{}".format(name), ref="master")
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
                        git.repo.delete_file("data/{}".format(name), "Script updating.", content.sha, branch="master")
                    except github.GithubException as e:
                        cprint("\n\tWARNING: GitHub API returned an error when requesting for '" + name + "' removal.\n"
                               "\t\tError Code: " + str(e.status) + "\nThis file may still be in the repo.", "yellow")
                    else:
                        print("\n\t" + igreen + "'" + name + "' successfully deleted.")
            return old_file_name
        else:
            print("\t➔ Deleting old file '" + old_file_name + "'...")
            try:
                content = git.repo.get_contents("data/{}".format(old_file_name), ref="master")
                git.repo.delete_file("data/{}".format(old_file_name), "Script updating.", content.sha, branch="master")
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
                content = git.repo.create_file("data/{}".format(new_file_name), "Script updating.", file_content,
                                               branch="master")
            except github.GithubException as e:
                if e.status == 422:
                    cprint("\n\tWARNING: GitHub API returned an error while requesting to add '" + new_file_name + "'."
                           "\n\t\t Error Code: 422 (the file was already in the repo).", "yellow")
                    sleep(0.6)
                    print("\n\t" + icyan + "'" + new_file_name + "' will be updated (not created).")
                    try:
                        content = git.repo.get_contents("data/{}".format(new_file_name), ref="master")
                        git.repo.update_file("data/{}".format(new_file_name), "Script updating.", file_content,
                                             content.sha, branch="master")
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
        print("\n\t➔ Creating '" + new_file_name + "'...")
        try:
            content = git.repo.create_file("data/{}".format(new_file_name), "Script updating.",
                                           file_content, branch="master")
        except github.GithubException as e:
            if e.status == 422:
                cprint("\n\tWARNING: GitHub API returned an error while requesting to add '" + new_file_name + "'."
                       "\n\t\t Error Code: 422 (the file was already in the repo).",
                       "yellow")
                sleep(0.6)
                print("\n\t" + icyan + "'" + new_file_name + "' will be updated (not created).")
                try:
                    content = git.repo.get_contents("data/{}".format(new_file_name), ref="master")
                    git.repo.update_file("data/{}".format(new_file_name), "Script updating.", file_content,
                                         content.sha, branch="master")
                except github.GithubException as e:
                    cprint("\n\tERROR: GitHub API returned an error when requesting for '" + new_file_name +
                           "' update.\n\t\t Error Code: " + str(e.status), "red")
                    sleep(0.6)
                    print("\n\t" + ired + "'" + new_file_name + "' cannot be updated.")
                    return None
                else:
                    print("\n\t" + igreen + "'" + new_file_name + "' successfully updated.")
                    return new_file_name
            else:
                cprint("\nERROR:\tGitHub API returned an error when requesting to add '" + new_file_name +
                       "' file.\n\t\t Error Code: " + str(e.status), "red")
                sleep(0.6)
                print("\n\t" + ired + "'" + new_file_name + "' cannot be created.")
                return None
        else:
            print("\n\t" + igreen + "'" + new_file_name + "' successfully created.")
        return new_file_name


def sorting_key(elem):
    return elem[list(elem.keys())[0]]


def toUpdate_updater(new_updated_files: dict, git: Git, from_editor: bool):
    s = "tables:\n"
    if not from_editor:
        req = requests.get("https://raw.githubusercontent.com/2ale2/scambifestival-ubjs/master/config/toUpdate.yml")
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
        cont = git.repo.get_contents("config/toUpdate.yml", ref="master")
    except github.GithubException as e:
        cprint("ERROR: GitHub API returned an error requesting for 'toUpdate.yml' content. I cannot upload it.\n"
               "Error code:\t" + str(e.status), "red")
    else:
        try:
            git.repo.update_file("config/toUpdate.yml", "Script configuration update.", s, cont.sha, branch="master")
        except github.GithubException as e:
            cprint("ERROR: GitHub API returned an error requesting for 'toUpdate.yml' content. I cannot upload it.\n"
                   "Error code:\t" + str(e.status), "red")
        else:
            print("\n" + igreen + "Configuration file 'toUpdate.yml' correctly updated!")

    if from_editor:
        print("\n" + iyallow + "Please note that it may take some minutes for changes to be applied on GitHub servers.")


def errors_handler(value: str):
    sleep(1.2)
    if value != "name" and value != "id" and value != "view_id" and value != "included" and value != "filters":
        cprint("\n\tERROR while getting '" + value + "' table infos."
               "\n\tPlease make sure to use the same word both in 'toUpdate.yml' and in 'tablesInfos.yml'.", "yellow")
        sleep(0.4)
        print("\nJumping to the next table...\n")
    else:
        cprint("\n\tERROR while getting the '" + value + "' info from table infos."
               "\n\tPlease make sure to add all the infos I need in the 'tablesInfos.yml' file.", "yellow")
        sleep(0.4)
        print("\nJumping to the next table...\n")
    sleep(0.7)


if __name__ == "__main__":
    main()
