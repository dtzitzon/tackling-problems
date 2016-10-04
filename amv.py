import nfldb
import sys
import getopt
import json 

from collections import defaultdict

# This is a script for computing the schedule-adjusted average margin
# of victory (AMV) for teams during a particular season.

usage = \
"""
Usage: python amv.py -y <season_year>
Options:
  -o <outfile> - optionally specify file to dump json results
"""
year = ''
outfile = ''
argv = sys.argv[1:]
try:
  opts, args = getopt.getopt(argv, "y:o:",["year=","ofile="])
except getopt.GetoptError:
  print usage
  sys.exit(2)
for opt, arg in opts:
  if opt in ('-y', '--year'):
    year = arg
  elif opt in ('-o', '--ofile'):
    outfile = arg
if year == '':
  print usage
  sys.exit(2)
  
POWER_RATING_ADJ = 100

db = nfldb.connect()
q = nfldb.Query(db)

# team ID to running differential
score_diffs = defaultdict(lambda: 0.0)

q.game(season_year=year, season_type='Regular')
games = q.as_games()

# add up total score differential per team
for g in games:
  diff = g.home_score - g.away_score
  score_diffs[g.home_team] += diff 
  score_diffs[g.away_team] -= diff

# divide by 16 total games to find AMV. TODO: adapt for incomplete seasons
amvs = {k: v/16 + POWER_RATING_ADJ for k, v, in score_diffs.items()} 

# adjust for oppoenent AMV
for team_id in amvs.keys():
  q = nfldb.Query(db)
  q.game(season_year=year, season_type='Regular', team=team_id)
  opp_amvs = []
  for g in q.as_games():
    opp = g.home_team if g.home_team != team_id else g.away_team
    opp_amvs.append(amvs[opp])
  
  # average AMV for all opponents
  opp_amv = sum(opp_amvs) / len(opp_amvs)
  
  # schedule adjustment to current AMV
  adj = POWER_RATING_ADJ - opp_amv
  
  amvs[team_id] += adj

if outfile != '':
  with open(outfile, 'w') as o:
    json.dump(amvs, o)
else:
  print amvs
