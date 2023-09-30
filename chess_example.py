from chess import ChessAPI
import matplotlib.pyplot as plt
import datetime as dt

# initialize API Object to
# pull historical data
c = ChessAPI("jaceiverson")

# declare you opponant
c.set_opp("bkoss326")

# find the matchup stats
df, d, r, m, ms = c.matchup_stats()

# plot results over time
ms.unstack(level=2).plot(
    kind="bar",
    stacked=True,
)
plt.show()

# win rates by month
month_win_rates = ms.groupby(level=1).apply(lambda x: x / float(x.sum()))

# plot it
# wins
ax = month_win_rates.loc[month_win_rates.index.get_level_values(2) == "win"].plot()

# loses
plt.plot(
    month_win_rates.loc[month_win_rates.index.get_level_values(2) == "loss"].values
)

# reference line at 50% for winrate
ax.axhline(y=0.5, linestyle="--", color="tab:orange")

# TODO plot x axis in a better format
# months = [dt.date(x[0],x[1],1) for x in ms.index]

plt.show()
