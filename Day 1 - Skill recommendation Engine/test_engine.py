from recommendation_engine import recommendation_levels
from data_loader import load_data

def test_recommendation():
    df = load_data()
    recommendations = recommendation_levels(97, df)
    assert len(recommendations) <= 3
    print("Test Passed!")

test_recommendation()