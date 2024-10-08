import argparse


def config_file_as_string(file_path):
    with open(file_path, 'r') as file:
        file_content = file.read()
    return file_content


def get_global_vars_of_config(config, delimiter):
    config_split = config.split(delimiter)
    result = config_split[1].strip().split('\n')[0]
    if ", " in result:
        return result.split(", ")
    else:
        return [result]


def read_vars_of_config_string(config):
    installation_path = get_global_vars_of_config(config, "# Installation path of Aurora")
    profile_name = get_global_vars_of_config(config, "# Profile Name")
    global_vors = get_global_vars_of_config(config, "# What VOR's do you want on every runway config?")
    global_ndbs = get_global_vars_of_config(config, "# What NDB's do you want on every runway config?")
    global_fixes = get_global_vars_of_config(config, "# What FIXES do you want on every runway config?")
    return [installation_path, profile_name, global_vors, global_ndbs, global_fixes]


def get_rwy_config_names(config):
    config_split = config.split("# On every line you can give a custom name for the configuration.")
    result = config_split[1].strip().split('\n\n')[0].split("\n")
    return result


def process_string(s):
    main_part, locations_part = s.split(": ")
    locations = locations_part.replace(", ", "; ").split("; ")
    processed_locations = [loc.split() for loc in locations]
    result = [main_part] + processed_locations
    return result


def get_rwy_per_rwy_config(config):
    rwy_split = config.split("# If you don't want to set the active RWY's for an airport, you don't have to write it")
    only_rwy_split = rwy_split[1].strip().split('\n\n')[0].split("\n")
    formatted_array = [process_string(s) for s in only_rwy_split]
    for entry in formatted_array:
        for loc in entry[1:]:
            loc[1:] = [x for x in loc[1:]]
    return formatted_array


def process_entry(entry):
    identifier, items_part = entry.split(": ")
    items = items_part.split(", ")
    return [identifier] + items


def get_values_per_rwy_config(config, value_type):
    string_split = ""
    if value_type == "VOR":
        string_split = config.split("# What VOR's do you want per runway config? Format: [name]: VOR 1, VOR 2, ...")
    if value_type == "NDB":
        string_split = config.split("# What NDB's do you want per runway config? Format: [name]: NDB 1, NDB 2, ...")
    if value_type == "FIX":
        string_split = config.split("# What FIXES do you want per runway config? Format: [name]: FIX 1, FIX 2, ...")
    if value_type == "REMARKS":
        string_split = config.split("# What ATIS remarks do you want per runway config? Format: [name]: Remarks")
    only_string_split = string_split[1].strip().split('\n\n')[0].split("\n")
    if only_string_split[0] == "NOTHING":
        return ""
    formatted_array = [process_entry(entry) for entry in only_string_split]
    return formatted_array


def find_element(name, array):
    result = []
    counter = 0
    for i in array:
        if i[0] == name:
            for j in range(len(array[counter])-1):
                result.append(i[j+1])
        counter += 1
    return result


def get_matrix_of_profiles(rwy_configs, global_config):
    matrix = []
    for config in rwy_configs:
        matrix.append([config, find_element(config, get_rwy_per_rwy_config(global_config)),
                       find_element(config, get_values_per_rwy_config(global_config, "VOR")),
                       find_element(config, get_values_per_rwy_config(global_config, "NDB")),
                       find_element(config, get_values_per_rwy_config(global_config, "FIX")),
                       find_element(config, get_values_per_rwy_config(global_config, "REMARKS"))])
    return matrix


def get_all_nav_points(file_path, nav_type):
    if nav_type == "FIX":
        file_path += "DE_FIXES.fix"
    if nav_type == "NDB":
        file_path += "DE_NDB.ndb"
    if nav_type == "VOR":
        file_path += "DE_VOR.vor"
    values = []
    with open(file_path, 'r') as file:
        for line in file:
            line = line.split('//')[0].strip()
            if line:
                value = line.split(';')[0].strip()
                values.append(value)
    return values


def profile_to_string(installation_path, profile_name):
    profile_file = installation_path + "/Profiles/" + profile_name + ".cpr"
    with open(profile_file, 'r') as file:
        file_content = file.read()
    return file_content


def remove_nav_points_from_global_vars(global_vars, vors, ndbs, fixes):
    new_vors = []
    new_ndbs = []
    new_fixes = []
    found = False
    for vor in vors:
        for global_vars_vor in global_vars[2]:
            if vor == global_vars_vor:
                found = True
        if not found:
            new_vors.append(vor)
        found = False
    for ndb in ndbs:
        for global_vars_ndb in global_vars[3]:
            if ndb == global_vars_ndb:
                found = True
        if not found:
            new_ndbs.append(ndb)
        found = False
    for fix in fixes:
        for global_vars_fix in global_vars[4]:
            if fix == global_vars_fix:
                found = True
        if not found:
            new_fixes.append(fix)
        found = False
    return [new_vors, new_ndbs, new_fixes]


def remove_navdata_per_rwyconfig(vors, ndbs, fixes, matrix_of_profiles, rwyconfig):
    new_vors = []
    new_ndbs = []
    new_fixes = []
    found = False
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


def replace_section(s, section_name, new_values):
    start = s.find(section_name)
    if start == -1:
        return s
    end = s.find("\n", start)
    if end == -1:
        end = len(s)
    return s[:start + len(section_name)] + new_values + s[end:]


def replace_navaids_in_string(s, fixes, vors, ndbs):
    fixes_str = ";".join(fixes) + ";"
    vors_str = ";".join(vors) + ";"
    ndbs_str = ";".join(ndbs) + ";"

    s = replace_section(s, "HideFIX=", fixes_str)
    s = replace_section(s, "HideVOR=", vors_str)
    s = replace_section(s, "HideNDB=", ndbs_str)

    return s


def get_new_remarks(matrix_of_profiles, rwyconfig):
    iterator = 0
    for profile in matrix_of_profiles:
        if rwyconfig == profile[0]:
            if matrix_of_profiles[iterator][5]:  # Check if Remarks are not empty
                return matrix_of_profiles[iterator][5][0]
        iterator += 1
    return False


def replace_atis_remarks_in_string(s, remarks):
    s = replace_section(s, "Remarks=", remarks)
    return s


def replace_atis_dep_and_arr_in_string(s, dep, arr):
    s = replace_section(s, "Takeoff=", dep)
    s = replace_section(s, "Landing=", arr)
    return s


def replace_file_content(file_path, new_content):
    with open(file_path, 'w') as file:
        file.write(new_content)


def get_runways_of_main_airport(matrix_of_profiles, main_airport_icao, rwyconfig):
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
                        if runway[0] == "d":
                            if len(runway) == 3:
                                dep.append(runway[1] + runway[2])
                            else:
                                dep.append(runway[1] + runway[2] + runway[3])
                        elif runway[0] == "a":
                            if len(runway) == 3:
                                arr.append(runway[1] + runway[2])
                            else:
                                arr.append(runway[1] + runway[2] + runway[3])
                    break
        iterator += 1
    iterator = 0
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


def set_manual_rwys(s, matrix_of_profiles, rwyconfig):
    iterator = 0
    airport_matrix = []
    result_string = ""
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

    for airport in airport_matrix:
        result_string = result_string + airport[0] + ":"
        for dep_rwy in airport[1]:
            result_string = result_string + dep_rwy[1] + dep_rwy[2]
            if len(dep_rwy) == 4:
                result_string += dep_rwy[3]
            if dep_rwy[0] == "e":
                result_string += ":1:1"
            elif dep_rwy[0] == "d":
                result_string += ":1:0"
        if not airport[2][0] == "":
            for arr_rwy in airport[2]:
                result_string = result_string + ";" + airport[0] + ":" + arr_rwy[1] + arr_rwy[2]
                if len(arr_rwy) == 4:
                    result_string += arr_rwy[3]
                result_string += ":0:1"
        result_string += ";"

    return replace_section(s, "RUNWAY_MANUAL=", result_string)


def main():
    parser = argparse.ArgumentParser(description="None")
    parser.add_argument('--rwyconfig', metavar="RWYCONFIG", type=str, help="Name of RWY Config")
    parser.add_argument('--configfile', metavar="RWYCONFIG", type=str, help="Name of Config file")
    args = parser.parse_args()

    config_file_path = "../configs/" + args.configfile
    config_file = config_file_as_string(config_file_path)

    global_vars = read_vars_of_config_string(config_file)
    matrix_of_profiles = get_matrix_of_profiles(get_rwy_config_names(config_file), config_file)

    icao_of_main_aiport = global_vars[1][0][0:4]

    path_of_nav_data = read_vars_of_config_string(config_file)[0][0]
    path_of_nav_data += "/SectorFiles/include/DE1/EDWW/NAV/"
    fixes = get_all_nav_points(path_of_nav_data, "FIX")
    ndbs = get_all_nav_points(path_of_nav_data, "NDB")
    vors = get_all_nav_points(path_of_nav_data, "VOR")

    profile_string = profile_to_string(read_vars_of_config_string(config_file)[0][0],
                                       read_vars_of_config_string(config_file)[1][0])

    nav_data_array = remove_nav_points_from_global_vars(global_vars, vors, ndbs, fixes)

    vors = nav_data_array[0]
    ndbs = nav_data_array[1]
    fixes = nav_data_array[2]

    nav_data_array = remove_navdata_per_rwyconfig(vors, ndbs, fixes, matrix_of_profiles, args.rwyconfig)

    vors = nav_data_array[0]
    ndbs = nav_data_array[1]
    fixes = nav_data_array[2]

    if not vors or not ndbs or not fixes:
        print("Error. Profile with name: \"" + args.rwyconfig + "\" does not exist in the config file.")
        return

    new_profile_string = replace_navaids_in_string(profile_string, fixes, vors, ndbs)

    remarks = get_new_remarks(matrix_of_profiles, args.rwyconfig)
    new_profile_string = replace_atis_remarks_in_string(new_profile_string, remarks)

    main_rwys = get_runways_of_main_airport(matrix_of_profiles, icao_of_main_aiport, args.rwyconfig)

    new_profile_string = replace_atis_dep_and_arr_in_string(new_profile_string, main_rwys[0], main_rwys[1])

    new_profile_string = set_manual_rwys(new_profile_string, matrix_of_profiles, args.rwyconfig)

    filepath_of_profile = global_vars[0][0] + "/Profiles/" + global_vars[1][0] + ".cpr"
    replace_file_content(filepath_of_profile, new_profile_string)


if __name__ == "__main__":
    main()
