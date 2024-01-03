# Python program to read
# json file
import csv
import json

# Opening JSON file
f = open('../data/sepakbola_detik.json')

# returns JSON object as
# a dictionary
data = json.load(f)

# Iterating through the json
# list

print(data['url'])
with open("../data/sepakbola_detik.csv", "w", encoding="utf-8", newline='') as file:
    writer = csv.writer(file)
    csv_datas = []
    for liga in data['data']:
        for liga_name in liga:
            # print(liga_name)
            # print(liga[liga_name])
            for teams in liga[liga_name]['data']:
                # print(teams)
                for team_name in teams:
                    # print(team_name)
                    # print(teams[team_name])
                    for player in teams[team_name]['data']:
                        # print(player)
                        for player_id in player:
                            # print(player_id)
                            # print(player[player_id])
                            csv_data = [
                                liga_name, liga[liga_name]['url'], liga[liga_name]['status'],
                                team_name, teams[team_name]['url'], teams[team_name]['status'],
                                player_id, player[player_id]['url'], player[player_id]['status']
                            ]
                            csv_datas.append(csv_data)
    writer.writerows(csv_datas)
# Closing file
f.close()
