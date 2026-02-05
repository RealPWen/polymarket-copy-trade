"""
End Time Estimator - Parse expected resolution time from market question.

Many Polymarket markets have predictable resolution times based on their title:
1. "Bitcoin Up or Down on July 7?" -> July 7, 18:00 UTC
2. "Warriors vs. Cavaliers" -> Game day, ~04:00-06:00 UTC (evening US time)
3. "Fed interest rate decision on January 29" -> January 29, ~22:00 UTC

This allows us to estimate closedTime WITHOUT prior knowledge, making V4 faster.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
import calendar


# Month name to number mapping
MONTHS = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12,
    'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6, 'jul': 7,
    'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
}


class EndTimeEstimator:
    """Estimate market resolution time from question text."""
    
    @staticmethod
    def parse_date_from_question(question: str, reference_year: int = 2025) -> Optional[datetime]:
        """
        Extract date from question text.
        
        Examples:
        - "Bitcoin Up or Down on July 7?" -> July 7
        - "Bitcoin above $89,000 on March 14?" -> March 14
        - "Fed decision on January 29" -> January 29
        """
        question_lower = question.lower()
        
        # Pattern 1: "on [Month] [Day]"
        pattern1 = r'on\s+([a-z]+)\s+(\d{1,2})\b'
        match = re.search(pattern1, question_lower)
        if match:
            month_str, day_str = match.groups()
            month = MONTHS.get(month_str)
            if month:
                day = int(day_str)
                try:
                    return datetime(reference_year, month, day)
                except ValueError:
                    pass
        
        # Pattern 2: "by [Month] [Day]"
        pattern2 = r'by\s+([a-z]+)\s+(\d{1,2})\b'
        match = re.search(pattern2, question_lower)
        if match:
            month_str, day_str = match.groups()
            month = MONTHS.get(month_str)
            if month:
                day = int(day_str)
                try:
                    return datetime(reference_year, month, day)
                except ValueError:
                    pass
        
        # Pattern 3: "[Month] [Day]" at end of question
        pattern3 = r'([a-z]+)\s+(\d{1,2})\s*\??$'
        match = re.search(pattern3, question_lower)
        if match:
            month_str, day_str = match.groups()
            month = MONTHS.get(month_str)
            if month:
                day = int(day_str)
                try:
                    return datetime(reference_year, month, day)
                except ValueError:
                    pass
        
        return None
    
    @staticmethod
    def get_market_type(question: str) -> str:
        """Classify market type based on question."""
        q = question.lower()
        
        # Crypto daily
        if any(x in q for x in ['bitcoin up or down', 'ethereum up or down', 
                                  'btc up or down', 'eth up or down',
                                  'bitcoin above', 'ethereum above']):
            return "crypto_daily"
        
        # Sports - NBA
        nba_teams = ['lakers', 'warriors', 'celtics', 'heat', 'knicks', 'mavericks',
                     'bulls', 'suns', 'nets', 'raptors', 'rockets', 'thunder',
                     'spurs', 'sixers', 'bucks', 'nuggets', 'clippers', 'hawks',
                     'kings', 'magic', 'pistons', 'cavaliers', 'hornets', 'pacers',
                     'grizzlies', 'pelicans', 'wizards', 'blazers', 'wolves', 'jazz',
                     'timberwolves']
        if any(team in q for team in nba_teams):
            return "nba"
        
        # Sports - MLB
        mlb_teams = ['yankees', 'dodgers', 'cubs', 'red sox', 'giants', 'cardinals',
                     'braves', 'mets', 'astros', 'phillies', 'padres', 'marlins',
                     'twins', 'rays', 'brewers', 'rangers', 'mariners', 'angels',
                     'rockies', 'nationals', 'pirates', 'reds', 'royals', 'tigers',
                     'white sox', 'blue jays', 'athletics', 'guardians', 'orioles', 'dbacks']
        if any(team in q for team in mlb_teams):
            return "mlb"
        
        # Fed/FOMC
        if any(x in q for x in ['fed ', 'fomc', 'interest rate', 'rate cut', 'rate hike']):
            return "fed"
        
        # Election
        if any(x in q for x in ['election', 'mayoral', 'gubernatorial', 'senate', 'congress']):
            return "election"
        
        return "unknown"
    
    @staticmethod
    def estimate_end_time(question: str, reference_year: int = 2025) -> Optional[Tuple[datetime, str]]:
        """
        Estimate end time from question.
        
        Returns: (estimated_datetime, market_type) or None
        """
        market_type = EndTimeEstimator.get_market_type(question)
        date = EndTimeEstimator.parse_date_from_question(question, reference_year)
        
        if market_type == "crypto_daily" and date:
            # Daily crypto markets close at 18:00 UTC
            return (datetime(date.year, date.month, date.day, 18, 0, 0), market_type)
        
        if market_type == "nba" and date:
            # NBA games typically end around 05:00 UTC (late evening US)
            return (datetime(date.year, date.month, date.day, 5, 0, 0), market_type)
        
        if market_type == "mlb" and date:
            # MLB games typically end around 04:00-05:00 UTC
            return (datetime(date.year, date.month, date.day, 5, 0, 0), market_type)
        
        if market_type == "fed" and date:
            # Fed meetings typically end around 22:00 UTC
            return (datetime(date.year, date.month, date.day, 22, 0, 0), market_type)
        
        if market_type == "election" and date:
            # Elections typically resolve late night (02:00 UTC next day)
            return (datetime(date.year, date.month, date.day, 2, 0, 0) + timedelta(days=1), market_type)
        
        return None
    
    @staticmethod
    def estimate_entry_window(question: str, reference_year: int = 2025) -> Optional[Tuple[datetime, datetime, str]]:
        """
        Estimate the optimal entry window for a market.
        
        Returns: (window_start, window_end, market_type) or None
        
        Window is typically 1-24 hours before expected resolution.
        """
        result = EndTimeEstimator.estimate_end_time(question, reference_year)
        if result is None:
            return None
        
        end_time, market_type = result
        
        # Define entry windows based on market type
        windows = {
            "crypto_daily": (6, 1),   # Enter 6-1 hours before close
            "nba": (4, 1),            # Enter 4-1 hours before
            "mlb": (4, 1),
            "fed": (2, 0.5),          # Enter 2-0.5 hours before (faster resolution)
            "election": (24, 6),      # Enter 24-6 hours before
        }
        
        hours_before_start, hours_before_end = windows.get(market_type, (6, 1))
        
        window_start = end_time - timedelta(hours=hours_before_start)
        window_end = end_time - timedelta(hours=hours_before_end)
        
        return (window_start, window_end, market_type)


def test_estimator():
    """Test the estimator with example questions."""
    examples = [
        "Bitcoin Up or Down on July 7?",
        "Ethereum Up or Down on August 29?",
        "Bitcoin above $89,000 on March 14?",
        "Warriors vs. Cavaliers",
        "Lakers vs. Thunder",
        "Fed decreases interest rates by 50 bps after January 2025 meeting",
        "Will Felipe Camozzato win the 2024 Porto Alegre mayoral election?",
        "Twins vs. Yankees",
        "Cubs vs. Giants",
    ]
    
    print("=" * 80)
    print("END TIME ESTIMATOR TEST")
    print("=" * 80)
    
    for q in examples:
        market_type = EndTimeEstimator.get_market_type(q)
        result = EndTimeEstimator.estimate_end_time(q)
        
        if result:
            end_time, _ = result
            print(f"\n{q[:50]}...")
            print(f"  Type: {market_type}")
            print(f"  Estimated end: {end_time.isoformat()}")
        else:
            print(f"\n{q[:50]}...")
            print(f"  Type: {market_type}")
            print(f"  Cannot estimate end time")


if __name__ == "__main__":
    test_estimator()
