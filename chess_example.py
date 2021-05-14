from chess import ChessAPI

c = ChessAPI('jaceiverson')
c.archive_grab()
df,d,r,m,ms = c.opp('EldrickLover')

#plot results over time
ms.unstack(level=2).plot(kind='bar',stacked=True,)
