import tkinter as tk
import subprocess
import json
import os
from os.path import join as pjoin
appdatapath = pjoin(os.getenv('LOCALAPPDATA'), "AuroraProfilePerRWYConfig")
os.makedirs(appdatapath, exist_ok=True)
configfilename = pjoin(appdatapath, "config.json")

DEFAULT_CONFIG = {
    'the_config_file_path': appdatapath + "\\" + "config_eddb.txt",
    'aurora_installation_path': "C:\\Aurora",
    'fir': "EDWW",
    'profile_name': "EDDH_TWR",
    'global_vors': ["HAM"],
    'global_ndbs': ["LYE"],
    'global_fixes': ["AMLUH"],
    'rwy_configs': [[["01"], ["EDDH"], ["BKD"], ["WSN"], ["IDEKO"], ["EXPECT"]]]
}


# Read given config file and returns it as a string
def config_file_as_string(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        file_content = file.read()
    return file_content


def load_config():
    config = DEFAULT_CONFIG.copy()
    try:
        with open(configfilename, "r", encoding='utf-8') as infile:
            written_config = json.load(infile)
        config.update(written_config)
    except FileNotFoundError:
        pass
    return config


def store_config(config):
    with open(configfilename, "w", encoding='utf-8') as outfile:
        json.dump(config, outfile, indent=4)


# Getting the vars of the config which should be on every RWY config in the profile per category
# Returns an array of all vars of a category
def get_global_vars_of_config(config, delimiter):
    config_split = config.split(delimiter)  # The delimiter is the comment above the 1st entry of each var
    result = config_split[1].strip().split('\n')[0]

    if ", " in result:
        return result.split(", ")
    else:
        return [result]


# Read the vars of the config which should be on every RWY config in the profile
# Returns an array of all global vars
def read_vars_of_config_string(config, config_json):
    installation_path = get_global_vars_of_config(config, "# The path:")
    profile_name = get_global_vars_of_config(config, "# Profile Name")
    global_vors = get_global_vars_of_config(config, "# Format: <VOR 1>[, <VOR 2>, <VOR 3>, ...]")
    global_ndbs = get_global_vars_of_config(config, "# Format: <NDB 1>[, <NDB 2>, <NDB 3>, ...]")
    global_fixes = get_global_vars_of_config(config, "# Format: <FIX 1>[, <FIX 2>, <FIX 3>, ...]")
    fir = get_global_vars_of_config(config, "# Format: <EDGG/EDMM/EDWW>")
    config_json['aurora_installation_path'] = installation_path[0]
    config_json['fir'] = fir[0]
    config_json['profile_name'] = profile_name[0]
    config_json['global_vors'] = global_vors
    config_json['global_ndbs'] = global_ndbs
    config_json['global_fixes'] = global_fixes
    return config_json


# Getting the names of the RWY configs the user given
def get_rwy_config_names(config):
    config_split = config.split("# [<Name X>]")
    result = config_split[1].strip().split('\n\n')[0].split("\n")

    return result


# Processes the lines of the given active RWY's
def process_string_for_rwy_config(s):
    main_part, locations_part = s.split(": ")
    locations = locations_part.replace(", ", "; ").split("; ")
    processed_locations = [loc.split() for loc in locations]
    result = [main_part] + processed_locations

    return result


# Gives a formatted array of given airports with their active runways
def get_rwy_per_rwy_config(config):
    rwy_split = config.split("# <Name X>: <airport ICAO 1> d<dep RWY 1>[ d<dep RWY 2> ...] a<arr RWY 1>[ a<arr RWY 2> "
                             "...][, <airport ICAO 2>...]")
    only_rwy_split = rwy_split[1].strip().split('\n\n')[0].split("\n")
    formatted_array = [process_string_for_rwy_config(s) for s in only_rwy_split]

    for entry in formatted_array:
        for loc in entry[1:]:
            loc[1:] = [x for x in loc[1:]]

    return formatted_array


# Processes the entries for given VOR's, NDB's, FIXES and Remarks in the config
def process_entry_per_rwy_config(entry):
    identifier, items_part = entry.split(": ")
    items = items_part.split(", ")

    return [identifier] + items


# Getting all NAV points and Remarks from the config
def get_values_per_rwy_config(config, value_type):
    string_split = ""
    if value_type == "VOR":
        string_split = config.split("# <Name X>: <VOR 1>[, <VOR 2>, <VOR 3>, ...]")
    elif value_type == "NDB":
        string_split = config.split("# <Name X>: <NDB 1>[, <NDB 2>, <NDB 3>, ...]")
    elif value_type == "FIX":
        string_split = config.split("# <Name X>: <FIX 1>[, <FIX 2>, <FIX 3>, ...]")
    elif value_type == "REMARKS":
        string_split = config.split("# <Name X>: <Remarks>")
    only_string_split = string_split[1].strip().split('\n\n')[0].split("\n")
    if only_string_split[0] == "NOTHING":  # If keyword NOTHING is written, it does nothing
        return ""

    formatted_array = [process_entry_per_rwy_config(entry) for entry in only_string_split]

    return formatted_array


# Returns VOR's, NDB's, FIXES or the Remarks as an array
def find_element(name, array):
    result = []
    counter = 0
    for i in array:
        if i[0] == name:
            for j in range(len(array[counter])-1):
                result.append(i[j+1])
        counter += 1

    return result


# A matrix where all preferences on each RWY config are saved in a certain structure
# The structure:
# [[RWY_config1, [[airport 1, RWY1, RWY2],[airport 2, ...]], [VOR's], [NDB's], [FIXES], [Remarks]], [[RWY_config2, ...]
def get_matrix_of_profiles(rwy_configs, global_config):
    matrix = []
    for config in rwy_configs:
        matrix.append([config, find_element(config, get_rwy_per_rwy_config(global_config)),
                       find_element(config, get_values_per_rwy_config(global_config, "VOR")),
                       find_element(config, get_values_per_rwy_config(global_config, "NDB")),
                       find_element(config, get_values_per_rwy_config(global_config, "FIX")),
                       find_element(config, get_values_per_rwy_config(global_config, "REMARKS"))])

    return matrix


# Getting all VOR's, NDB's or FIXES from the sector file
def get_all_nav_points(file_path, nav_type):
    if nav_type == "FIX":
        file_path += "DE_FIXES.fix"
    elif nav_type == "NDB":
        file_path += "DE_NDB.ndb"
    elif nav_type == "VOR":
        file_path += "DE_VOR.vor"

    values = []

    with open(file_path, 'r', encoding='utf-8') as file:  # Reading the sector file
        for line in file:
            line = line.split('//')[0].strip()
            if line:
                value = line.split(';')[0].strip()
                values.append(value)

    return values


# Converts the profile file to a string
def profile_to_string(installation_path, profile_name):
    profile_file = installation_path + "/Profiles/" + profile_name + ".cpr"

    with open(profile_file, 'r', encoding='utf-8') as file:
        file_content = file.read()

    return file_content


# Takes all NAV points from the sector file and removes the NAV points which were defined in the config file
# In Aurora you have to write every NAV point to hide. Shown NAV points are not displayed in the profile file
# Returns all NAV points which are left
def remove_nav_points_from_config(config, vors, ndbs, fixes):
    new_vors = []
    new_ndbs = []
    new_fixes = []
    found = False

    for vor in vors:
        for config_vor in config['global_vors']:
            if vor == config_vor:
                found = True
        if not found:
            new_vors.append(vor)
        found = False

    for ndb in ndbs:
        for config_ndb in config['global_ndbs']:
            if ndb == config_ndb:
                found = True
        if not found:
            new_ndbs.append(ndb)
        found = False

    for fix in fixes:
        for config_fix in config['global_fixes']:
            if fix == config_fix:
                found = True
        if not found:
            new_fixes.append(fix)
        found = False

    return [new_vors, new_ndbs, new_fixes]


# Takes all NAV points which are left from the NAV points which should be shown on every RWY config and removes the NAV
# points depending on the RWY config
def remove_navdata_per_rwyconfig(vors, ndbs, fixes, matrix_of_profiles, rwyconfig):
    # All NAV points which are left after removal per RWY config
    new_vors = []
    new_ndbs = []
    new_fixes = []
    found = False  # Indicator if the NAV point were found
    iterator = 0

    for profile in matrix_of_profiles:
        if rwyconfig == profile[0]:
            if matrix_of_profiles[iterator][2]:  # Check if VORs are not empty
                for vor in vors:
                    for profile_matrix_vor in matrix_of_profiles[iterator][2]:
                        if vor == profile_matrix_vor:
                            found = True
                    if not found:
                        new_vors.append(vor)
                    found = False
            else:
                new_vors = vors
            if matrix_of_profiles[iterator][3]:  # Check if NDBs are not empty
                for ndb in ndbs:
                    for profile_matrix_ndb in matrix_of_profiles[iterator][3]:
                        if ndb == profile_matrix_ndb:
                            found = True
                    if not found:
                        new_ndbs.append(ndb)
                    found = False
            else:
                new_ndbs = ndbs
            if matrix_of_profiles[iterator][4]:  # Check if FIXES are not empty
                for fix in fixes:
                    for profile_matrix_fix in matrix_of_profiles[iterator][4]:
                        if fix == profile_matrix_fix:
                            found = True
                    if not found:
                        new_fixes.append(fix)
                    found = False
            else:
                new_fixes = fixes
        iterator += 1

    return [new_vors, new_ndbs, new_fixes]


# Replaces a single line with a given string
# For example if a format in the profile looks like this: "HideFIX=FIX1;FIX2;FIX3;..." it takes the "HideFIX=" to
# indicate where to replace something in the profile file and replaces the part after it with a given string
# Returns the whole profile string as result
def replace_section(s, section_name, new_values):
    start = s.find(section_name)
    if start == -1:
        return s
    end = s.find("\n", start)
    if end == -1:
        end = len(s)
    return s[:start + len(section_name)] + new_values + s[end:]


# Replaces the hidden NAV points from the profile with the ones that should be hidden via the config file
def replace_navaids_in_string(s, fixes, vors, ndbs):
    # Formatting all NAV points to this format: POINT1;POINT2;POINT3;...;
    fixes_str = ";".join(fixes) + ";"
    vors_str = ";".join(vors) + ";"
    ndbs_str = ";".join(ndbs) + ";"

    s = replace_section(s, "HideFIX=", fixes_str)
    s = replace_section(s, "HideVOR=", vors_str)
    s = replace_section(s, "HideNDB=", ndbs_str)

    return s


# Returns the remarks of a specific RWY config
def get_new_remarks(matrix_of_profiles, rwyconfig):
    iterator = 0

    for profile in matrix_of_profiles:
        if rwyconfig == profile[0]:
            if matrix_of_profiles[iterator][5]:  # Check if Remarks are not empty
                return matrix_of_profiles[iterator][5][0]
        iterator += 1

    return False


# Replaces the ATIS Remarks, Takeoff and Landing section from the profile string
def replace_atis_remarks_dep_arr_in_string(s, remarks, dep, arr, is_fis_or_ctr):
    s = replace_section(s, "Remarks=", remarks)
    if not is_fis_or_ctr:
        s = replace_section(s, "Takeoff=", dep)
        s = replace_section(s, "Landing=", arr)

    return s


# Takes the new profile string and writes it into the profile file
def replace_file_content(file_path, new_content):
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(new_content)


# Returns the RWY's as string from the main airport for the ATIS
def get_runways_of_main_airport(matrix_of_profiles, main_airport_icao, rwyconfig, is_fis_or_ctr):
    if is_fis_or_ctr:
        return [0, 0]

    dep = []
    arr = []
    dep_str = ""
    arr_str = ""
    iterator = 0

    for rwyprofile in matrix_of_profiles:
        if rwyprofile[0] == rwyconfig:
            for airport in matrix_of_profiles[iterator][1]:
                if airport[0] == main_airport_icao:
                    for runway in airport:
                        runway_str = runway[1] + runway[2]
                        if len(runway) == 4:
                            runway_str += runway[3]
                        if runway[0] == "d":
                            dep.append(runway_str)
                        elif runway[0] == "a":
                            arr.append(runway_str)
                    break
        iterator += 1

    iterator = 0

    # Adding " " between the departure and arrival RWY's if there are multiple ones
    for dep_rwy in dep:
        if not iterator == 0:
            dep_str += " "
        dep_str += dep_rwy
        iterator += 1

    iterator = 0

    for arr_rwy in arr:
        if not iterator == 0:
            arr_str += " "
        arr_str += arr_rwy
        iterator += 1

    return [dep_str, arr_str]


# Setting the manual RWY's to be selected in the "AIRPORTS" menu
def set_manual_rwys(s, matrix_of_profiles, rwyconfig):
    iterator = 0
    airport_matrix = []
    result_string = ""

    # Getting the departure and arrival runways
    # The beginning of the RWY's indicate how is it used
    # d: Only departure, a: Only arrival, e: Departure and arrival
    for rwyprofile in matrix_of_profiles:
        if rwyprofile[0] == rwyconfig:
            for airport in matrix_of_profiles[iterator][1]:
                airport_entry = []
                dep_rwys = []
                arr_rwys = []
                for runway in airport:
                    if runway[0].isupper():
                        airport_entry.append(runway)
                    elif runway[0] == "d":
                        dep_rwys.append(runway)
                    elif runway[0] == "a":
                        arr_rwys.append(runway)
                iterator2 = 0
                for dep_rwy in dep_rwys:
                    for arr_rwy in arr_rwys:
                        if (len(dep_rwy) == 3) & (len(arr_rwy) == 3):
                            if dep_rwy[1] + dep_rwy[2] == arr_rwy[1] + arr_rwy[2]:
                                dep_rwys[iterator2] = "e" + dep_rwy[1] + dep_rwy[2]
                        elif (len(dep_rwy) == 4) & (len(arr_rwy) == 4):
                            if dep_rwy[1] + dep_rwy[2] + dep_rwy[3] == arr_rwy[1] + arr_rwy[2] + arr_rwy[3]:
                                dep_rwys[iterator2] = "e" + dep_rwy[1] + dep_rwy[2] + dep_rwy[3]
                    iterator2 += 1
                airport_entry.append(dep_rwys)
                airport_entry.append(arr_rwys)
                airport_matrix.append(airport_entry)
        iterator += 1

    iterator = 0
    iterator2 = 0

    # Removing the arrival RWY's which are used as Departure and Arrival at once
    # The RWY's which are used for both at once an indicated as "e" in the beginning of the string
    for airport in airport_matrix:
        for arr_rwy in airport[2]:
            for dep_rwy in airport[1]:
                if len(arr_rwy) == 3:
                    if (arr_rwy[1] + arr_rwy[2]) == (dep_rwy[1] + dep_rwy[2]):
                        airport_matrix[iterator][2][iterator2] = ""
                elif len(arr_rwy) == 4:
                    if (arr_rwy[1] + arr_rwy[2] + arr_rwy[3]) == (dep_rwy[1] + dep_rwy[2] + dep_rwy[3]):
                        airport_matrix[iterator][2][iterator2] = ""
            iterator2 += 1
        iterator2 = 0
        iterator += 1

    # Building the string with the format of how the active RWYs are set in the profile
    # This is the format:
    # 1:0: Used only for departure
    # 0:1: Used only for arrival
    # 1:1: Used for both
    # <ICAO1>:<RWY1>:<[1:0]/[0:1]/[1:1];<ICAO2>...;
    # Example: EDDH:33:1:0;EDDH:23:0:1;EDHI:23:1:1;EDHL:25:1:1;
    for airport in airport_matrix:
        for dep_rwy in airport[1]:
            result_string = result_string + airport[0] + ":" + dep_rwy[1] + dep_rwy[2]
            if len(dep_rwy) == 4:
                result_string += dep_rwy[3]
            if dep_rwy[0] == "e":
                result_string += ":1:1"
            elif dep_rwy[0] == "d":
                result_string += ":1:0"
            result_string += ";"
        if not airport[2][0] == "":
            for arr_rwy in airport[2]:
                result_string = result_string + ";" + airport[0] + ":" + arr_rwy[1] + arr_rwy[2]
                if len(arr_rwy) == 4:
                    result_string += arr_rwy[3]
                result_string += ":0:1"
            result_string += ";"

    return replace_section(s, "RUNWAY_MANUAL=", result_string)


# Check if given profile is a CTR or FIS profile
def is_ctr_or_fis_profile(profile_name):
    atc_position = profile_name[len(profile_name) - 3:]
    if atc_position == "FIS" or atc_position == "CTR":
        return True
    else:
        return False


# String for the naming of the RWY Config
main_string = ""


# Modifies string as input for the RWY config
def modify_string(new_value, root, path):
    global main_string
    main_string = new_value  # Changes the string for the chosen RWY config name

    # Open Aurora
    subprocess.Popen(fr'{path}\Aurora.exe', cwd=path)

    # Close window
    root.destroy()


def main():
    config = load_config()
    
    global main_string

    # Loading the wished config file as a string
    config_file_path = config['the_config_file_path']
    config_file = config_file_as_string(config_file_path)

    # Saving the vars which should be on every RWY config into the config JSON
    config = read_vars_of_config_string(config_file, config)

    # The info if the given profile is a FIS or CTR profile
    is_fis_or_ctr = is_ctr_or_fis_profile(config['profile_name'])

    # Saving the vars which should be on a specific RWY config as multidimensional array
    config['rwy_configs'] = get_matrix_of_profiles(get_rwy_config_names(config_file), config_file)

    # The 4 letter ICAO code from the main airport or the FIR. Using the first 4 letters from the profile
    icao_of_main_airport = config['profile_name'][0:4]

    # Getting all NAV points
    path_of_nav_data = config['aurora_installation_path']
    path_of_nav_data = path_of_nav_data.replace('\\', '/')
    path_of_nav_data = path_of_nav_data + "/SectorFiles/include/DE1/" + config['fir'] + "/NAV/"
    
    fixes = get_all_nav_points(path_of_nav_data, "FIX")
    ndbs = get_all_nav_points(path_of_nav_data, "NDB")
    vors = get_all_nav_points(path_of_nav_data, "VOR")

    # The profile file as a string
    profile_string = profile_to_string(config['aurora_installation_path'], config['profile_name'])
    
    # Removing the NAV points which should be displayed on every RWY config
    nav_data_array = remove_nav_points_from_config(config, vors, ndbs, fixes)
    vors = nav_data_array[0]
    ndbs = nav_data_array[1]
    fixes = nav_data_array[2]

    # Create GUI window
    root = tk.Tk()
    root.title("IVAO Aurora Profile per RWY Config")
    root.geometry("400x400")
    root.configure(bg="white")

    # Header label
    label = tk.Label(root, text=f"Choose your Runway Config:", bg="white", wraplength=350)
    label.pack(pady=20)

    # Buttons for RWY Configs
    rwy_config_names = [sublist[0] for sublist in config['rwy_configs']]
    button1 = tk.Button(
        root,
        text="   " + rwy_config_names[0] + "   ",
        command=lambda: modify_string(rwy_config_names[0], root, config['aurora_installation_path'])
    )
    button1.pack(pady=5)
    if len(rwy_config_names) > 1:
        button2 = tk.Button(
            root,
            text="   " + rwy_config_names[1] + "   ",
            command=lambda: modify_string(rwy_config_names[1], root, config['aurora_installation_path'])
        )
        button2.pack(pady=5)
    if len(rwy_config_names) > 2:
        button3 = tk.Button(
            root,
            text="   " + rwy_config_names[2] + "   ",
            command=lambda: modify_string(rwy_config_names[2], root, config['aurora_installation_path'])
        )
        button3.pack(pady=5)
    if len(rwy_config_names) > 3:
        button4 = tk.Button(
            root,
            text="   " + rwy_config_names[3] + "   ",
            command=lambda: modify_string(rwy_config_names[3], root, config['aurora_installation_path'])
        )
        button4.pack(pady=5)
    if len(rwy_config_names) > 4:
        button5 = tk.Button(
            root,
            text="   " + rwy_config_names[4] + "   ",
            command=lambda: modify_string(rwy_config_names[4], root, config['aurora_installation_path'])
        )
        button5.pack(pady=5)
    if len(rwy_config_names) > 5:
        button6 = tk.Button(
            root,
            text="   " + rwy_config_names[5] + "   ",
            command=lambda: modify_string(rwy_config_names[5], root, config['aurora_installation_path'])
        )
        button6.pack(pady=5)
    if len(rwy_config_names) > 6:
        button7 = tk.Button(
            root,
            text="   " + rwy_config_names[6] + "   ",
            command=lambda: modify_string(rwy_config_names[6], root, config['aurora_installation_path'])
        )
        button7.pack(pady=5)
    if len(rwy_config_names) > 7:
        button8 = tk.Button(
            root,
            text="   " + rwy_config_names[7] + "   ",
            command=lambda: modify_string(rwy_config_names[7], root, config['aurora_installation_path'])
        )
        button8.pack(pady=5)
    if len(rwy_config_names) == 9:
        button9 = tk.Button(
            root,
            text="   " + rwy_config_names[8] + "   ",
            command=lambda: modify_string(rwy_config_names[8], root, config['aurora_installation_path'])
        )
        button9.pack(pady=5)

    # Start GUI
    root.mainloop()

    # Setting the current RWY config
    rwy_config = main_string

    # Removing the NAV points which should be displayed on a specific RWY config
    nav_data_array = remove_navdata_per_rwyconfig(vors, ndbs, fixes, config['rwy_configs'], rwy_config)
    vors = nav_data_array[0]
    ndbs = nav_data_array[1]
    fixes = nav_data_array[2]

    # If the given RWY config name does not exist, the hidden NAV points will be empty
    if not vors or not ndbs or not fixes:
        print("Error. Profile with name: \"" + rwy_config + "\" does not exist in the config file.")
        return

    # Replacing the NAV points from the profile string
    new_profile_string = replace_navaids_in_string(profile_string, fixes, vors, ndbs)

    # Getting the remarks for a specific RWY config
    remarks = get_new_remarks(config['rwy_configs'], rwy_config)

    # Getting the main RWYs for a specific RWY config
    main_rwys = get_runways_of_main_airport(config['rwy_configs'], icao_of_main_airport, rwy_config, is_fis_or_ctr)

    # Replacing the ATIS remarks and main RWY's from the profile string
    new_profile_string = replace_atis_remarks_dep_arr_in_string(new_profile_string, remarks, main_rwys[0],
                                                                main_rwys[1], is_fis_or_ctr)

    # Replacing the active RWY's displayed in the "AIRPORTS" menu in the profile string
    new_profile_string = set_manual_rwys(new_profile_string, config['rwy_configs'], rwy_config)

    # Taking the new profile string and replacing it with the text which were on the old profile file
    filepath_of_profile = config['aurora_installation_path'] + "/Profiles/" + config['profile_name'] + ".cpr"
    replace_file_content(filepath_of_profile, new_profile_string)
    
    store_config(config)


if __name__ == "__main__":
    main()
