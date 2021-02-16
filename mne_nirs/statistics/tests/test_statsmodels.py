# Authors: Robert Luke <mail@robertluke.net>
#
# License: BSD (3-clause)

import numpy as np
import pytest
import pandas as pd
import statsmodels.formula.api as smf

from ...simulation import simulate_nirs_raw
from ...experimental_design import make_first_level_design_matrix
from ...statistics import run_GLM, statsmodels_to_results
from ...utils._io import glm_to_tidy


@pytest.mark.parametrize('func', ('mixedlm', 'ols', 'rlm'))
@pytest.mark.filterwarnings('ignore:.*optimization.*:')
@pytest.mark.filterwarnings('ignore:.*on the boundary.*:')
def test_statsmodel_to_df(func):
    func = getattr(smf, func)
    np.random.seed(0)

    amplitude = 1.432

    df_cha = pd.DataFrame()
    for n in range(5):

        raw = simulate_nirs_raw(sfreq=3., amplitude=amplitude,
                                sig_dur=300., stim_dur=5.,
                                isi_min=15., isi_max=45.)
        design_matrix = make_first_level_design_matrix(raw, stim_dur=5.0)
        glm_est = run_GLM(raw, design_matrix)
        with pytest.warns(RuntimeWarning, match='Non standard source detect'):
            cha = glm_to_tidy(raw, glm_est, design_matrix)
        cha["ID"] = '%02d' % n
        df_cha = df_cha.append(cha)
    df_cha["theta"] = df_cha["theta"] * 1.0e6
    roi_model = func("theta ~ -1 + Condition", df_cha,
                     groups=df_cha["ID"]).fit()
    df = statsmodels_to_results(roi_model)
    assert type(df) == pd.DataFrame
    assert df["Coef."]["Condition[A]"] == amplitude
    assert df["Significant"]["Condition[A]"]
    assert df.shape == (8, 8)

    roi_model = smf.rlm("theta ~ -1 + Condition", df_cha,
                        groups=df_cha["ID"]).fit()
    df = statsmodels_to_results(roi_model)
    assert type(df) == pd.DataFrame
    assert df["Coef."]["Condition[A]"] == amplitude
    assert df["Significant"]["Condition[A]"]
    assert df.shape == (8, 8)
