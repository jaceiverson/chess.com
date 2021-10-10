"""Chess.com API Wrapper"""
import datetime as dt
from typing import Optional, Any

import requests as r
import pandas as pd


class ChessAPI:
    """Wrapper Class"""

    def __init__(self, username: str) -> None:
        self.user: str = username

        self.base_url: str = "https://api.chess.com/pub/player"
        # your opponent you want to compare to
        self.opp: Optional[str] = None
        self.opps: dict[Optional[str], Any] = {}
        # pull the historical data and save it to a pd.df
        # named self.game_history
        self._archive_grab()

    def get_all_archive_urls(self) -> dict[str, list[str]]:
        """Return a list of all API endpoints for a given user"""
        return self.__pull(
            f"https://api.chess.com/pub/player/{self.user}/games/archives"
        )

    def set_opp(self, opp_name: str) -> None:
        """Set the name of your opponent"""
        self.opp = opp_name

    @staticmethod
    def __pull(url: str) -> dict[Any, Any]:
        """
        requests library to pull the json
        """
        return r.get(url).json()

    @staticmethod
    def _clean_result(results: dict[Any, Any], color: str) -> tuple[str, Optional[str]]:
        """
        returns the result of the match and the detail behind it
        """
        res_string = results[color]["result"]
        if res_string in ["checkmated", "resigned", "timeout", "lose"]:
            return "loss", res_string
        if res_string in ["agreed", "repetition", "50move"]:
            return "draw", res_string
        if res_string == "stalemate":
            return res_string, res_string
        if res_string == "win":
            return (
                res_string,
                results["white" if color == "black" else "black"]["result"],
            )
        return res_string, None

    def _extract_data(self, api_obj: dict[Any, Any]) -> dict[str, Any]:
        """
        sets the values for the df

        looks in the api json response to determine the following columns

        color, opp (name), your result, your detailed result, current rating,
        opp current rating, the date the game concluded
        """
        if api_obj["white"]["username"] == self.user:
            color = "white"
            result, result_detail = self._clean_result(api_obj, "white")
            rating = api_obj["white"]["rating"]
            opp = api_obj["black"]["username"]
            opp_rating = api_obj["black"]["rating"]

        else:
            color = "black"
            result, result_detail = self._clean_result(api_obj, "black")
            rating = api_obj["black"]["rating"]
            opp = api_obj["white"]["username"]
            opp_rating = api_obj["white"]["rating"]

        return {
            "color": color,
            "opp": opp,
            "result": result,
            "result detail": result_detail,
            "current rating": rating,
            "opp current rating": opp_rating,
            "game-mode": api_obj["time_class"] + "-" + api_obj["time_control"],
            "rated": api_obj["rated"],
            "url": api_obj["url"],
            "date": dt.datetime.fromtimestamp(api_obj["end_time"]).date(),
        }

    def _archive_grab(self) -> None:
        """
        pulls all the data found in all archive pages
        """
        self.data = []
        for page in self.get_all_archive_urls()["archives"]:
            self.data += self.__pull(page)["games"]

        self.game_history = pd.DataFrame()
        for row in self.data:
            self.game_history = self.game_history.append(
                pd.DataFrame.from_records([self._extract_data(row)])
            )

        self.game_history["date"] = pd.to_datetime(self.game_history["date"])

    @staticmethod
    def find_number_of_moves(result_dict: dict[Any, Any]) -> int:
        """parse PGN to find number of moves in the game"""
        return result_dict["pgn"].split("\n\n")[1].count(".")

    def matchup_stats(self) -> tuple[Any, Any, Any, Any, Any]:
        """
        returns grouped data (date,result,result detail) between you and
        a specific player
        """
        try:
            opp_df = self.game_history.loc[self.game_history["opp"] == self.opp].copy()
        except AttributeError:
            raise AttributeError("Please declare opponent name using self.set_opp")

        def group(opp_data: pd.DataFrame, cols: list[Any]) -> pd.DataFrame:
            """
            group a pandas df by columns,
            add a "pct" column,
            return newly created df
            """
            df = opp_data.groupby(cols).count()[opp_data.columns[0]].copy()
            df.name = "results"
            df = pd.DataFrame(df)
            df["pct"] = df / df.sum()
            return df

        month = group(
            opp_df,
            [
                pd.Index(opp_df["date"]).year,
                pd.Index(opp_df["date"]).month,
                "result",
                "result detail",
            ],
        )

        month_simple = month.groupby(
            [
                month.index.get_level_values(0),
                month.index.get_level_values(1),
                month.index.get_level_values(2),
            ]
        ).sum()["results"]

        detail = month.groupby(
            [month.index.get_level_values(2), month.index.get_level_values(3)]
        ).sum()

        results = detail.groupby(detail.index.get_level_values(0)).sum()

        self.opps[self.opp] = {
            "raw": opp_df,
            "detail": detail,
            "results": results,
            "month": month,
            "month-s": month_simple,
        }

        return opp_df, detail, results, month, month_simple
