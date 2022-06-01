# FND_twitter application
This is a terminal based fake news detection application implemented as part of my thesis.

## File structure
There are three main folders on the root level. The data_conversion_and_scrape_scripts folder contains the scripts used for scraping data from the internet and processing certain data. The model_contruction_testing folder contains the .ipynb file which was used for model contruction, training and testing. The twitter_fnd_project folder contains the actual fake news detection application. It contains 4 files and 5 subfolders. There descriptions are as follows:

- ***main.py***: This file controls how the application is run
- ***core_functions.py***: This file contains the main operating logics including tweets retrival, processing, learning, analysing and so on.
- ***process_text.py***: This file contains functions which are used to process the tweet text to get them ready for learning and analysing.
- ***util.py***: This file contains lots of utility functions which are used by functions in the other files.
- ***config folder***: This folder contains multiple configuration files that are used by the program, including credentials and search details.
- ***models folder***:  This folder contains the TCN model (excluded in Github due to size limit).
- ***fake folder***:  This folder contains all the fake tweets and hashtags found.
- ***real folder***:  This folder contains all the real tweets found.
- ***user folder***: This folder contains the user file.

## Usage instruction
To run this application, the user simply needs to navigate to the twitter_fnd_project folder in terminal and do "python3 main.py" followed by one or more command line arguments. When the user user "ALL", the program will run in inspector mode which will search for fake news based on the search details contained in the configuration files. If the user inputs anything else, the program will run in user mode and search according to those keywords. Separate files will be generated for every unique keyword combinations.

# Packages/libraries needed to be installed to run this application
- tweepy
- pandas
- numpy
- langdetect
- transformers
- nltk (some additional sub-packages may need to be downloaded based on the feedback from the program)
- tensorflow
- tcn

# Download links:
You can choose to form the datasets and train the model yourself or use the ones below.
- Combined training set: https://drive.google.com/file/d/1wbyil6LIoCaKibMHOMZHK8WpJVfaRRlQ/view?usp=sharing
- Pre-trained model: https://drive.google.com/file/d/10KNB6UWZ1Z4jpV-10yLIF50JR_Kd1Ahq/view?usp=sharing
