# ABC codes adopted from https://github.com/rcmorehead/simpleabc/blob/master/simple_abc.py

import random
import settings
import numpy as np
from models_single_product import market

random.seed()

SENTINEL = object()


class ABC_GenerativeModel(market):
    """
    Base class for constructing models for approximate bayesian computing
    inherits the market and implements the following additional methods:
    * Model.draw_theta
    * Model.generate_data
    * Model.summary_stats
    * Model.distance_function
    """

    def __init__(self, params={}):
        super(ABC_GenerativeModel, self).__init__(params)
        self.fixed_params['input_type'] = 'histograms'
        self.fixed_params['input_histograms_are_normalized'] = True
        self.params['input_type'] = 'histograms'
        self.params['input_histograms_are_normalized'] = True

    def set_data(self, data):
        self.data = data
        self.data_summary_stats = self.summary_stats(self.data)

    def set_epsilon(self, epsilon):
        """
        A method to give the model object the value of epsilon if your model
        code needs to know it.
        """
        self.epsilon = epsilon

    def generate_data_and_reduce(self, theta):
        """
        A combined method for
        (i) generating data,
        (ii) calculating summary statistics
        (iii) and evaluating the distance function
        """
        synthetic_data = self.generate_data(theta)
        synthetic_summary_stats = self.summary_stats(synthetic_data)
        distance = self.distance_function(synthetic_summary_stats, self.data_summary_stats)

        return distance

    def draw_theta(self):
        """
        Sub-classable method for drawing from a prior distribution.
        This method should return an array-like iterable that is a vector of
        proposed model parameters from your prior distribution.
        """
        theta = np.random.choice(np.linspace(0,2,10))
        return theta

    def generate_data(self, theta):
        """
        Sub-classable method for generating synthetic data sets from forward
        model.
        This method should return an array/matrix/table of simulated data
        taking vector theta as an argument.
        """
        # self.fixed_params['rate_decision_threshold'] = theta
        data = self.generateTimeseries(theta, get_percieved_qualities_and_avg_reviews=False, do_not_return_df=True)
        print('synthetic', data)
        return data

    def summary_stats(self, data):
        """
        Sub-classable method for computing summary statistics.
        This method should return an array-like iterable of summary statistics
        taking an array/matrix/table as an argument
        """
        # return np.asarray(data.iloc[-1])
        return np.asarray(data[-1])

    def distance_function(self, summary_stats, summary_stats_synth):
        """
        Sub-classable method for computing a distance function.
        This method should return a distance D of for comparing to the
        acceptance tolerance (epsilon) taking two array-like iterables of
        summary statistics as an argument (nominally the observed summary
        statistics and .
        """
        distance = 0.2*sum(abs(summary_stats-summary_stats_synth))
        return distance

    def process_observed_timeseries(observed_timeseries, input_type='histograms', do_not_return_torchtensor_or_df=True):
        """Returns time series of histograms"""
        assert do_not_return_torchtensor_or_df, 'in ABC we do not work with data-frames or tensors'
        if input_type == 'histograms':
            all_ratings = list(observed_timeseries['Rating'])
            current_histogram = [0] * settings.params['number_of_rating_levels']
            histogram_timeseries = [[0] * settings.params['number_of_rating_levels']]
            for rating in all_ratings:
                current_histogram[rating - 1] += 1
                append_histogram = copy.deepcopy(current_histogram)
                histogram_timeseries.append(append_histogram)
        # df = pd.DataFrame(histogram_timeseries)
        return histogram_timeseries


################################################################################
#########################    ABC Algorithms   ##################################
################################################################################

def basic_abc(model, data, epsilon=1, min_samples=10):
    # ,
    #           parallel=False, n_procs='all', pmc_mode=False,
    #           weights='None', theta_prev='None', tau_squared='None'):
    """
    Perform Approximate Bayesian Computation (ABC) on a data set given a
    forward model.
    ABC is a likelihood-free method of Bayesian inference that uses simulation
    to approximate the true posterior distribution of a parameter. It is
    appropriate to use in situations where:
    The likelihood function is unknown or is too computationally
    expensive to compute.
    There exists a good forward model that can produce data sets
    like the one of interest.
    It is not a replacement for other methods when a likelihood
    function is available!
    Parameters
    ----------
    model : object
        A model that is a subclass of simpleabc.Model
    data  : object, array_like
        The "observed" data set for inference.
    epsilon : float, optional
        The tolerance to accept parameter draws, default is 1.
    min_samples : int, optional
        Minimum number of posterior samples.
    parallel : bool, optional
        Run in parallel mode. Default is a single thread.
    n_procs : int, str, optional
        Number of subprocesses in parallel mode. Default is 'all' one for each
        available core.
    pmc_mode : bool, optional
        Population Monte Carlo mode on or off. Default is False. This is not
        meant to be called by the user, but is set by simple_abc.pmc_abc.
    weights : object, array_like, str, optional
        Importance sampling weights from previous PMC step. Used  by
        simple_abc.pmc_abc only.
    theta_prev : object, array_like, str, optional
        Posterior draws from previous PMC step.  Used by simple_abc.pmc_abc
        only.
    tau_squared : object, array_like, str, optional
        Previous Gaussian kernel variances. for importance sampling. Used by
        simple_abc.pmc_abc only.
    Returns
    -------
    posterior : numpy array
        Array of posterior samples.
    distances : object
        Array of accepted distances.
    accepted_count : float
        Number of  posterior samples.
    trial_count : float
        Number of total samples attempted.
    epsilon : float
        Distance tolerance used.
    weights : numpy array
        Importance sampling weights. Returns an array of 1s where
        size = posterior.size when not in pmc mode.
    tau_squared : numpy array
        Gaussian kernel variances. Returns an array of 0s where
        size = posterior.size when not in pmc mode.
    eff_sample : numpy array
        Effective sample size. Returns an array of 1s where
        size = posterior.size when not in pmc mode.
    Examples
    --------
    Forth coming.
    """

    posterior, rejected, distances = [], [], []
    trial_count, accepted_count = 0, 0

    data_summary_stats = model.summary_stats(data)
    model.set_epsilon(epsilon)

    while accepted_count < min_samples:
        trial_count += 1

        # if pmc_mode:
        #     theta_star = theta_prev[:, np.random.choice(
        #                             xrange(0, theta_prev.shape[1]),
        #                             replace=True, p=weights/weights.sum())]
        #
        #     theta = stats.multivariate_normal.rvs(theta_star, tau_squared)
        #     if np.isscalar(theta) == True:
        #         theta = [theta]
        #
        #
        # else:
        #     theta = model.draw_theta()

        theta = model.draw_theta()

        synthetic_data = model.generate_data(theta)

        synthetic_summary_stats = model.summary_stats(synthetic_data)

        distance = model.distance_function(data_summary_stats,
                                           synthetic_summary_stats)

        if distance < epsilon:
            accepted_count += 1
            posterior.append(theta)
            distances.append(distance)

        else:
            pass
            #rejected.append(theta)

    posterior = np.asarray(posterior).T

    if len(posterior.shape) > 1:
        n = posterior.shape[1]
    else:
        n = posterior.shape[0]


    # weights = np.ones(n)
    # tau_squared = np.zeros((posterior.shape[0], posterior.shape[0]))
    # eff_sample = n

    return (posterior, distances,
            accepted_count, trial_count,
            epsilon)#, weights, tau_squared, eff_sample)