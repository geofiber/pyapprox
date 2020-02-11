r"""
Approximate Control Variate Monte Carlo
=======================================
This tutorial builds upon :ref:`sphx_glr_auto_examples_plot_control_variate_monte_carlo.py` and describes how to implement and deploy *approximate* control variate Monte Carlo (ACVMC) sampling to compute expectations of model output from multiple models. CVMC is often not useful for practical analysis of numerical models because typically the mean of the lower fidelity model, i.e. :math:`\mu_\V{\kappa}` is unknown and the cost of the lower fidelity model is non trivial. These two issues can be overcome by using approximate control variate Monte Carlo.

This tutorial also demonstrates that multi-level Monte Carlo and multi-fidelity Monte Carlo are both approximate control variate techniques and how this understanding can be used to improve their efficiency.

Let the cost of the high fidelity model per sample be 1 and let the cost of the low fidelity model be :math:`r_\V{\kappa}\ge1`. Now lets use :math:`N` samples to estimate :math:`Q_{\V{\alpha},N}` and :math:`Q_{\V{\kappa},N}` and these  :math:`N` samples plus another :math:`rN` samples to estimate :math:`\mu_{\V{\kappa}}` so that

.. math::

   \mu_{\V{\kappa},N,r}=\frac{1}{rN}\sum_{i=1}^{rN}Q_\V{\kappa}

and

.. math::

   Q_{\V{\alpha},N,r}^{\text{ACV}}=Q_{\V{\alpha},N} + \eta \left( Q_{\V{\kappa},N} - \mu_{\V{\kappa},N,r} \right)


The cost of computing the ACV estimator is

.. math::

   C_\mathrm{cv} = N + (1+r_\V{\kappa})N

With this sampling scheme we have

.. math::

  Q_{\V{\kappa},N} - \mu_{\V{\kappa},N,r}&=\frac{1}{N}\sum_{i=1}^N f_\V{\kappa}^{(i)}-\frac{1}{rN}\sum_{i=1}^{rN}f_\V{\kappa}^{(i)}\\
  &=\frac{1}{N}\sum_{i=1}^N f_\V{\kappa}^{(i)}-\frac{1}{rN}\sum_{i=1}^{N}f_\V{\kappa}^{(i)}-\frac{1}{rN}\sum_{i=N}^{rN}f_\V{\kappa}^{(i)}\\
  &=\frac{r-1}{rN}\sum_{i=1}^N f_\V{\kappa}^{(i)}-\frac{1}{rN}\sum_{i=N}^{rN}f_\V{\kappa}^{(i)}\\

where for ease of notation we write :math:`r_\V{\kappa}N` and :math:`\lfloor r_\V{\kappa}N\rfloor` interchangibly.
Using the above expression yields

.. math::
   \var{\left( Q_{\V{\kappa},N} - \mu_{\V{\kappa},N,r}\right)}&=\mean{\left(\frac{r-1}{rN}\sum_{i=1}^N f_\V{\kappa}^{(i)}-\frac{1}{rN}\sum_{i=N}^{rN}f_\V{\kappa}^{(i)}\right)^2}\\
  &=\frac{(r-1)^2}{r^2N^2}\sum_{i=1}^N \var{f_\V{\kappa}^{(i)}}+\frac{1}{r^2N^2}\sum_{i=N}^{rN}\var{f_\V{\kappa}^{(i)}}\\
  &=\frac{(r-1)^2}{r^2N^2}N\var{f_\V{\kappa}}+\frac{1}{r^2N^2}(r-1)N\var{f_\V{\kappa}}\\
  %&=\left(\frac{(r-1)^2}{r^2N}+\frac{(r-1)}{r^2N}\right)\var{f_\V{\kappa}}\\
  &=\frac{r-1}{r}\frac{\var{f_\V{\kappa}}}{N}

where we have used the fact that since the samples between the first and second term on the first line are not shared the covariance is zero. Also we have

.. math::

  \covar{Q_{\V{\alpha},N}}{\left( Q_{\V{\kappa},N} - \mu_{\V{\kappa},N,r}\right)}=\covar{\frac{1}{N}\sum_{i=1}^N f_\V{\alpha}^{(i)}}{\frac{r-1}{rN}\sum_{i=1}^N f_\V{\kappa}^{(i)}-\frac{1}{rN}\sum_{i=N}^{rN}f_\V{\kappa}^{(i)}}

The correlation between the estimators :math:`\frac{1}{N}\sum_{i=1}^{N}Q_\V{\alpha}` and :math:`\frac{1}{rN}\sum_{i=N}^{rN}Q_\V{\kappa}` is zero because the samples used in these estimators are different for each model. Thus

.. math::

   \covar{Q_{\V{\alpha},N}}{\left( Q_{\V{\kappa},N} - \mu_{\V{\kappa},N,r}\right)} &=\covar{\frac{1}{N}\sum_{i=1}^N f_\V{\alpha}^{(i)}}{\frac{r-1}{rN}\sum_{i=1}^N f_\V{\kappa}^{(i)}}\\
  &=\frac{r-1}{r}\frac{\covar{f_\V{\alpha}}{f_\V{\kappa}}}{N}

Recalling the variance reduction of the CV estimator using the optimal :math:`\eta` is

.. math::

   \gamma &= 1-\frac{\covar{Q_{\V{\alpha},N}}{\left( Q_{\V{\kappa},N} - \mu_{ \V{\kappa},N,r}\right)}^2}{\var{\left( Q_{\V{\kappa},N} - \mu_{\V{\kappa},N,r}\right)}\var{Q_{\V{\alpha},N}}}\\
   &=1-\frac{N^{-2}\frac{(r-1)^2}{r^2}\covar{f_\V{\alpha}}{f_\V{\kappa}}}{N^{-1}\frac{r-1}{r}\var{f_\V{\kappa}}N^{-1}\var{f_\V{\alpha}}}\\
   &=1-\frac{r-1}{r}\corr{f_\V{\alpha}}{f_\V{\kappa}}^2

which is found when :math:`\eta=(\gamma-1)\var{f_\V{\alpha}}`
"""
#%%
# Lets setup the problem and compute an ACV estimate of :math:`\mean{f_0}`
import pyapprox as pya
import numpy as np
import matplotlib.pyplot as plt
from pyapprox.tests.test_control_variate_monte_carlo import TunableExample
from scipy.stats import uniform

np.random.seed(1)
univariate_variables = [uniform(-1,2),uniform(-1,2)]
variable = pya.IndependentMultivariateRandomVariable(univariate_variables)
shifts=[.1,.2]
model = TunableExample(np.pi/2*.95,shifts=shifts)
exact_integral_f0=0

nhf_samples = int(1e1)
nsample_ratio = 10
samples_shared = pya.generate_independent_random_samples(
    variable,nhf_samples)
samples_lf_only = pya.generate_independent_random_samples(
    variable,nhf_samples*nsample_ratio)
values0 = model.m0(samples_shared)
values1_shared = model.m1(samples_shared)
values1_lf_only = model.m1(samples_lf_only)

cov = model.get_covariance_matrix()
gamma = 1-(nsample_ratio-1)/nsample_ratio*cov[0,1]**2/(cov[0,0]*cov[1,1])
eta = (gamma-1)*cov[0,0]
acv_mean = values0.mean()+eta*(values1_shared.mean()-values1_lf_only.mean())
print('MC difference squared =',(values0.mean()-exact_integral_f0)**2)
print('ACVMC difference squared =',(acv_mean-exact_integral_f0)**2)

#%%
#Now lets compute the variance reduction for different sample sizes
def compute_acv_two_model_variance_reduction(nsample_ratio):
    ntrials=1000
    means = np.empty((ntrials,2))
    for ii in range(ntrials):
        samples_shared = pya.generate_independent_random_samples(
            variable,nhf_samples)
        samples_lf_only = pya.generate_independent_random_samples(
            variable,nhf_samples*nsample_ratio)
        values0 = model.m0(samples_shared)
        values1_shared = model.m1(samples_shared)
        values1_lf_only = model.m1(samples_lf_only)
        means[ii,0]= values0.mean()
        gamma=1-(nsample_ratio-1)/nsample_ratio*cov[0,1]**2/(cov[0,0]*cov[1,1])
        eta = (gamma-1)*cov[0,0]
        means[ii,1]=values0.mean()+eta*(
            values1_shared.mean()-values1_lf_only.mean())

    print("Theoretical ACV variance reduction",
          1-(nsample_ratio-1)/nsample_ratio*cov[0,1]**2/(cov[0,0]*cov[1,1]))
    print("Achieved ACV variance reduction",
          means[:,1].var(axis=0)/means[:,0].var(axis=0))

compute_acv_two_model_variance_reduction(10)
compute_acv_two_model_variance_reduction(200)
#%%
#For a fixed number of high-fidelity evaluations :math:`N` the ACVMC variance reduction will converge to the CVMC variance reduction. Try changing :math:`N`.

print("Theoretical CV variance reduction",1-cov[0,1]**2/(cov[0,0]*cov[1,1]))

#%%
#Control variate Monte Carlo can be easily extended and applied to more than two models. Consider :math:`M` lower fidelity models with sample ratios :math:`r_\alpha>=1`, for :math:`\alpha=1,\ldots,M`. The approximate control variate estimator of the mean of the high-fidelity model :math:`Q_0=\mean{f_0}` is
#
#.. math::
#   Q^{\text{ACV}} &= Q_{0,\mathcal{Z}_{0,1}} + \sum_{\alpha=1}^M \eta_\alpha \left( Q_{\alpha,\mathcal{Z}_{\alpha,1}} - \mu_{\alpha,\mathcal{Z}_{\alpha,2}} \right) =Q_{0,\mathcal{Z}_{0,1}} + \sum_{\alpha=1}^M \eta_\alpha \Delta_{\alpha,\mathcal{Z}_{\alpha,1},\mathcal{Z}_{\alpha,2}}\\&=Q_{0,N}+\V{\eta}\V{\Delta}
#
#Here :math:`\V{\eta}=[\eta_1,\ldots,\eta_M]^T`, :math:`\V{\Delta}=[\Delta_1,\ldots,\Delta_M]^T`, and :math:`\mathcal{Z}_{\alpha,1}`, :math:`\mathcal{Z}_{\alpha,2}` are sample sets that may or may not be disjoint. Specifying the exact nature of these sets, including their cardinality, can be used to design different ACV estimators which will discuss later.
#
#The variance of the ACV estimator is
#
#.. math::
#
#   \var{Q^{\text{ACV}}} = \var{Q_{0}}\left(1+\V{\eta}^T\frac{\covar{\V{\Delta}}{\V{\Delta}}}{\var{Q_0}}\V{\eta}+2\V{\eta}^T\frac{\covar{\V{\Delta}}{Q_0}}{\var{Q_0}}\right)
#
#The control variate weights that produce the minimum variance are given by
#
#.. math::
#
#   \V{\eta} = -\covar{\V{\Delta}}{\V{\Delta}}^{-1}\covar{\V{\Delta}}{Q_0}
#
#The resulting variance reduction is
#
#.. math::
#
#   \gamma =1-\covar{\V{\Delta}}{Q_0}^T\frac{\covar{\V{\Delta}}{\V{\Delta}}}{\var{Q_0}}\covar{\V{\Delta}}{Q_0}
#
#

#%%
#Multi-level Monte Carlo (MLMC)
#------------------------------
#
#Total cost is
#
#.. math::
#
#   C_{\mathrm{tot}}=\sum_{l=1}^L C_lr_lN_1
#   
#Variance of estimator is
#
#.. math::
#  
#   \var{Q_L}=\sum_{l=1}^L \var{Y_l}r_lN_1
#   
#Treating :math:`r_l` as a continuous variable the variance of the MLMC estimator is minimized for a fixed budget :math:`C` by setting
#
#.. math::
#
#   N_l=r_lN_1=\sqrt{\var{Y_l}/C_l}
#   
#Choose L so that
#
#.. math::
#   
#   \left(\mean{Q_L}-\mean{Q}\right)^2<\frac{1}{2}\epsilon^2
#   
#Choose :math:`N_l` so total variance
#
#.. math::
#   \var{Q_L}<\frac{1}{2}\epsilon^2
#
#Multi-fidelity Monte Carlo (MFMC)
#---------------------------------
#
#.. math::
#   
#   r_i=\left(\frac{C_1(\rho^2_{1i}-\rho^2_{1i+1})}{C_i(1-\rho^2_{12})}\right)^{\frac{1}{2}}
#   
#Let :math:`C=(C_1\cdots C_L)^T r=(r_1\cdots r_L)^T` then
#
#.. math::
#
#   N_1=\frac{C_{\mathrm{tot}}}{C^Tr} & & N_i=r_iN_1\\
#
#  
#The control variate weights are
#
#.. math::
#   
#   \alpha_i=\frac{\rho_{1i}\sigma_1}{\sigma_i}

#%%
#References
#^^^^^^^^^^
#.. [PWGSIAM2016] `B. Peherstorfer, K. Willcox, M. Gunzburger, Optimal model management for multifidelity Monte Carlo estimation, SIAM J. Sci. Comput. 38 (2016) 59 A3163–A3194. <https://doi.org/10.1137/15M1046472>`_
#
#.. [CGSTCVS2011] `K.A. Cliffe, M.B. Giles, R. Scheichl, A.L. Teckentrup, Multilevel Monte Carlo methods and applications to elliptic PDEs with random coefficients, Comput. Vis. Sci. 14 (2011) <https://doi.org/10.1007/s00791-011-0160-x>`_
#
#.. [GilesOR2008] `M.B. Giles, Multilevel Monte Carlo path simulation, Oper. Res. 56 (2008) 607–617. <https://doi.org/10.1287/opre.1070.0496>`_