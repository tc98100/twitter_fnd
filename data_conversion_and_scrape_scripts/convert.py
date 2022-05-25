# import os, json
# import pandas as pd
#
# path_to_json = 'somedir/'
# json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]
# print(json_files)  # for me this prints ['foo.json']


import os
import pandas as pd

folder_names = ["gurlitt-all-rnr-threads", "sydneysiege-all-rnr-threads", "ottawashooting-all-rnr-threads", "putinmissing-all-rnr-threads",
"charliehebdo-all-rnr-threads", "ferguson-all-rnr-threads", "ebola-essien-all-rnr-threads", "prince-toronto-all-rnr-threads", "germanwings-crash-all-rnr-threads"]
sub_folder_names = ["non-rumours", "rumours"]

for folder_name in folder_names:
    for sub_folder_name in sub_folder_names:
        file_paths = []
        for path, currentDirectory, files in os.walk("./" + folder_name + "/" + sub_folder_name):
            for file in files:
                if file.endswith('.json') and "source-tweets" in path:
                    file_paths.append(os.path.join(path, file))

        dataframes = []

        for file_path in file_paths:
            dataframes.append(pd.read_json(file_path))

        if len(dataframes) != 0:
            combined = pd.concat(dataframes, ignore_index=True, sort=False)
            combined = combined.drop_duplicates(subset='text', ignore_index=True)
            combined = combined[['text']]
            if sub_folder_name == "non-rumours":
                combined['class'] = 1
            else:
                combined['class'] = 0

            combined.to_csv(folder_name.replace("all-rnr-threads", "") + sub_folder_name + ".csv", index=False)
