# github action reference https://github.com/actions/setup-python

import json
from classes.goal_id import GoalID
from classes.tempo_co import TempoCo
#from classes.info_pemilu import InfoPemilu

def main():
    #config
    limit = 5
    #goal indonesia
    goal_id = GoalID()
    goal_id.process(limit=limit)

    with open("./data/goal_id.json", "w") as external_file:
        external_file.write(json.dumps(goal_id.result))
        external_file.close()

    #tempo.co
    tempo_co = TempoCo()
    tempo_co.process(limit=limit)

    with open("./data/tempo_co.json", "w") as external_file:
        external_file.write(json.dumps(tempo_co.result))
        external_file.close()

    # # info pemilu
    # info_pemilu = InfoPemilu()
    # info_pemilu.process(jenis_dewan='dpd')
    # info_pemilu.process(jenis_dewan='dpr')
    # info_pemilu.process(jenis_dewan='dprdp')
    # info_pemilu.process(jenis_dewan='dprdk')

main()
