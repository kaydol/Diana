# Diana
Diana is a game bot written on Python 2.7. She's not completely finished and there are many issues yet to be resolved. Besides those issues, there are quite a number of limitations in using her, and she will take control of your PC while active. 

She's originally designed to be used under one OS (Windows) with one screen resolution (1920x1080) and a limited set of available ATs. Majority of stuff was brutally hardcoded to fit given resolution and a specific game version, so Diana is extremely vulnerable for any game UI update.

## What she can
- Order assault groups to engage in nearest battles
- Retreat groups to rear if they need rest and\or reinforcements
- Reinforce groups once they've reached a safe place and let them rest 
- Redeploy assault groups in random town if they were destroyed, and then send them to frontline
- Simulate being active to prevent getting disconnected from the server for being AFK

## Downsides
- Diana can't tell (yet) if her commanding skills raise or waste warfunds, and, truth to be told, she mostly wastes them (since she plays nearly as good as an average player, that fact made me doubt if it's even possible to effectively raise warfunds playing solely on strategic map).
- While moving an assault team, Diana sends it without checking if team might encounter enemy towns on the way, she sends them straight to the point of interest. If there's an enemy town in between team and a destination, attacking team will create a new battle, while retreating team might get destroyed or surrender.

## Possible improvements
- If **text recognizing** was implemented, Diana would be able to keep notes of changes in ammount of warfunds and stop or change her tactic if she's wasting money. Text recognizing would also allow to deploy assault groups in the town closest to the frontline and provide possibilities for implementing a cross-resolution solution.
- **Building a graph of towns** based solely on screenshots is a very complicated task, but that would allow to implement better assault group navigation and building routes with multiple milestones, yeilding awesome possibilities for safer retreating as well as more sophisticated attack strategies.
