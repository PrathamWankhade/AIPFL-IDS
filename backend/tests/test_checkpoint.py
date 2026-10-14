"""Regression: test metrics must describe the deployed checkpoint (P0)."""
from pathlib import Path

TRAIN = Path(__file__).resolve().parents[1] / "train.py"


def test_evaluate_runs_on_reloaded_deployed_model():
    src = TRAIN.read_text()
    i_copy = src.find("shutil.copyfile(best_path, model_path)")
    i_load = src.find("tf.keras.models.load_model(str(model_path))")
    i_eval = src.find("evaluate_model(deployed_model, X_test, y_test")
    assert i_copy != -1 and i_load != -1 and i_eval != -1, "promotion+reload+evaluate sequence missing"
    assert i_copy < i_load < i_eval, "must promote, reload from disk, then evaluate once"
    assert "result[\"model\"], X_test" not in src, "must not evaluate the in-memory last-round model"
