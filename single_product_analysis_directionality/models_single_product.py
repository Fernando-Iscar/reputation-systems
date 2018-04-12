# generative model for reviews
# this version is used to generate the histogram of reviews for a particular product over time, irrespective of the
# choice of a particular product among many. There is a single decision to purchase or not to purchase that each consumer
# faces, follwed by a decision to leave a review or not.
# The parameters are the parameters of a single product.

import torch
import pymc as mc
import numpy as np
import random as RD
import scipy.stats as st
import pandas as pd
import copy
import pickle

RD.seed()


class product():

    def __init__(self):
        self.set_missing_product_params()

    def set_missing_product_params(self):
        # if 'product_indices' not in  self.fixed_params: # product indices not useful for just one product.
        #     self.params['product_indices'] = list(range(self.params['number_of_products']))
        if 'number_of_rating_levels' not in self.fixed_params:
            self.params['number_of_rating_levels'] = 5
        if 'price' not in self.fixed_params:
            self.params['price'] = 10
        if 'product_features' not in self.fixed_params:
            self.params['product_features'] = dict.fromkeys(['feature'])
            self.params['product_features']['feature'] = [20]
        if 'neutral_quality' not in self.fixed_params:
            self.params['neutral_quality'] = 3
        if 'quality_std' not in self.fixed_params:
            self.params['quality_std'] = 1.5
        if 'true_quality' not in self.fixed_params:
            self.params['true_quality'] = np.random.normal(self.params['neutral_quality'],
                                                           self.params['quality_std'])
        if 'product_tracked' not in self.fixed_params:
            self.params['product_tracked'] = 0  # the product whose histograms we ae analyzing

        if 'input_type' not in self.fixed_params:
            self.params['input_type'] = 'histograms'#'averages'  # train the network with the average of reviews rather than
            # the full histogram of reviews

        if 'input_histograms_are_normalized' not in self.fixed_params:
            self.params['input_histograms_are_normalized'] = False  # histograms are normalized to the frequencies
            # rather than showing the total counts
        if 'value_of_outside_option' not in self.fixed_params:
            self.params['value_of_outside_option'] = 0.0  # Whenever the expected utility exceeds the value of the
            # outside option, the product is purchased.
        if 'testing_what' not in self.fixed_params:
            self.params['testing_what'] = 'threshold_directionality'  # We can either test for BM vs Motivation or test
            # for threshold_positive_zero or use ABC to determine threshold_directionality


class consumer(product):
    def __init__(self):
        super(consumer, self).__init__()
        self.set_missing_consumer_params()


    def set_missing_consumer_params(self):
        if 'tendency_to_rate' not in self.fixed_params:
            self.params['tendency_to_rate'] = 0.2
        if 'number_of_rating_levels' not in self.fixed_params:
            self.params['number_of_rating_levels'] = 5
        if 'consumer_fit_std' not in self.fixed_params:
            self.params['consumer_fit_std'] = 4.5
        if 'consumer_fit_distribution' not in self.fixed_params:
            self.params['consumer_fit_distribution'] = st.norm(0, self.params['consumer_fit_std'])

        # if 'consumer_comparison_mode' not in self.fixed_params:
        #     self.params['consumer_comparison_mode'] should not be set here, it should be set in set_random_params
        # because it is the subject of inference.

    def init_consumer_private_parameters(self):
        self.consumer_private_fit = self.params['consumer_fit_distribution'].rvs()
        self.consumer_private_alpha = np.random.normal(self.params['population_alpha'][0],
                                                       self.params['population_alpha'][1])
        self.consumer_private_beta = dict.fromkeys(self.params['population_beta'].keys())
        for i in self.params['population_beta'].keys():
            self.consumer_private_beta[i] = np.random.normal(self.params['population_beta'][i][0],
                                                             self.params['population_beta'][i][1])

    def make_purchase(self):
        product_is_purchased = False

        features_utility = 0
        for i in self.params['product_features'].keys():
            features_utility += self.consumer_private_beta[i + '_beta'] * np.array(self.params['product_features'][i])

        price_utility = self.consumer_private_alpha * np.array(self.params['price'])

        expected_utility = features_utility + price_utility + self.percieved_qualities[-1] + self.consumer_private_fit

        # print(expected_utility)
        if expected_utility > self.params['value_of_outside_option']:
            product_is_purchased = True
        # print(product_is_purchased)
        return product_is_purchased

    def evaluate_product(self):

        if self.params['consumer_comparison_mode'] == 'BM':
            review_levels = [self.percieved_qualities[-1] - 1.5, self.percieved_qualities[-1] - 0.5,
                             self.percieved_qualities[-1] + 0.5,
                             self.percieved_qualities[-1] + 1.5]

            experienced_quality = self.params['true_quality'] + self.consumer_private_fit

            product_review = int(1 + sum(1.0 * (experienced_quality >= np.array(review_levels))))
            # print(self.params['consumer_comparison_mode'])

        elif self.params['consumer_comparison_mode'] == 'motivation':

            if self.avg_reviews:  # it is not the first review, avg_reviews is not an empty list
                review_levels = [self.avg_reviews[-1] - 1.5, self.avg_reviews[-1] - 0.5,
                                 self.avg_reviews[-1] + 0.5, self.avg_reviews[-1] + 1.5]
            else:
                review_levels = [self.params['neutral_quality'] - 1.5, self.params['neutral_quality'] - 0.5,
                                 self.params['neutral_quality'] + 0.5, self.params['neutral_quality'] + 1.5]

            experienced_quality = self.params['true_quality'] + self.consumer_private_fit

            product_review = int(1 + sum(1.0 * (experienced_quality >= np.array(review_levels))))

            # print(self.params['consumer_comparison_mode'])

        else:
            raise Exception("consumer_comparison_mode not set!")

        return product_review

        review_levels = [self.percieved_qualities[-1] - 1.5, self.percieved_qualities[-1] - 0.5,
                         self.percieved_qualities[-1] + 0.5,
                         self.percieved_qualities[-1] + 1.5]

        experienced_quality = self.params['true_quality'] + self.consumer_private_fit

        product_review = int(1 + sum(1.0 * (experienced_quality >= np.array(review_levels))))

        return product_review

    def decide_to_rate(self, product_review):

        if self.params['consumer_comparison_mode'] == 'BM':
            if np.random.binomial(1, self.params['tendency_to_rate']):
                decision = True
            elif self.avg_reviews:  # it is not the first review, avg_reviews is not an empty list
                decision = (abs(product_review - self.percieved_qualities[-1]) > self.params['rate_decision_threshold']) \
                           and (np.random.binomial(1, min(3 * self.params['tendency_to_rate'], 1)))
            else:
                decision = True

            # print(self.params['consumer_comparison_mode'],decision)

        if self.params['consumer_comparison_mode'] == 'motivation':
            if np.random.binomial(1, self.params['tendency_to_rate']):
                decision = True
            elif self.avg_reviews:  # it is not the first review, avg_reviews is not an empty list
                decision = (abs(product_review - self.avg_reviews[-1]) > self.params['rate_decision_threshold']) \
                           and (np.random.binomial(1, min(3 * self.params['tendency_to_rate'], 1)))
            else:
                decision = True

            # print(self.params['consumer_comparison_mode'],decision)

        return decision


class market(consumer):
    def __init__(self, params={}):
        self.fixed_params = copy.deepcopy(params)
        self.params = copy.deepcopy(params)
        self.set_missing_market_params()
        super(market, self).__init__()

    def set_missing_market_params(self):
        if 'population_beta' not in self.fixed_params:
            self.params['population_beta'] = dict.fromkeys(['feature_beta'])
            self.params['population_beta']['feature_beta'] = [np.random.uniform(1, 2), 1]
        if 'population_alpha' not in self.fixed_params:
            self.params['population_alpha'] = [np.random.uniform(-3, -2), 1]
        if 'total_number_of_reviews' not in self.fixed_params:
            self.params['total_number_of_reviews'] = 20

    def set_random_params(self, theta=None):
        """Randomly sets the parameters that are the subject of inference by the inference engine.
        The parameters are randomized according to the prior distributions"""

        if self.params['testing_what'] == 'BM vs Motivation':
            self.params['consumer_comparison_mode'] = RD.choice(['BM', 'motivation'])
            if 'rate_decision_threshold' not in self.fixed_params:
                self.params['rate_decision_threshold'] = 1

        elif self.params['testing_what'] == 'threshold_positive_zero':
            self.params['rate_decision_threshold'] = RD.choice([-1.0, 1.0])
            if 'consumer_comparison_mode' not in self.fixed_params:
                self.params['consumer_comparison_mode'] = 'BM'
        elif self.params['testing_what'] == 'threshold_directionality':
            assert theta is not None, "theta not supplied for threshold_directionality"
            self.params['rate_decision_threshold'] = theta
            if 'consumer_comparison_mode' not in self.fixed_params:
                self.params['consumer_comparison_mode'] = 'BM'
        else:
            raise Exception("testing_what is undefined!")

    def init_reputation_dynamics(self):

        self.percieved_qualities = []
        self.reviews = []
        self.avg_reviews = []
        self.histogram_reviews = [0] * self.params['number_of_rating_levels']
        self.percieved_qualities = []

        self.customer_count = 0
        self.purchase_decisions = []
        self.purchase_count = 0

    def form_perception_of_quality(self):

        if self.avg_reviews:
            quality_anchor = self.avg_reviews[-1]
        else:
            quality_anchor = self.params['neutral_quality']

        observed_histograms = self.histogram_reviews

        infer_quality = mc.Normal('infer_quality', mu=self.params['neutral_quality'],
                                  tau=1/(self.params['quality_std']**2))  # this is the prior on the quality

        data = observed_histograms

        @mc.stochastic(observed=True)
        def histogram_mental_model(value=data, infer_quality=infer_quality):

            return np.sum(
                np.log(
                    (self.params['consumer_fit_distribution'].cdf(quality_anchor - 1.5 - infer_quality)) ** value[0]) +
                np.log(
                    (self.params['consumer_fit_distribution'].cdf(quality_anchor - 0.5 - infer_quality) -
                     self.params['consumer_fit_distribution'].cdf(quality_anchor - 1.5 - infer_quality)) ** value[1]) +
                np.log(
                    (self.params['consumer_fit_distribution'].cdf(quality_anchor + 0.5 - infer_quality) -
                     self.params['consumer_fit_distribution'].cdf(quality_anchor - 0.5 - infer_quality)) ** value[2]) +
                np.log(
                    (self.params['consumer_fit_distribution'].cdf(quality_anchor + 1.5 - infer_quality) -
                     self.params['consumer_fit_distribution'].cdf(quality_anchor + 0.5 - infer_quality)) ** value[3]) +
                np.log(
                    (1 - self.params['consumer_fit_distribution'].cdf(quality_anchor + 1.5 - infer_quality)) ** value[
                        4]))

        model = mc.MCMC([infer_quality, histogram_mental_model])
        model.sample(iter=100, progress_bar=False)
        self.percieved_qualities += [np.mean(model.trace('infer_quality')[:])]

    def step(self):
        self.init_consumer_private_parameters()
        # fixing the common prior on quality at the beginning of perception:
        if 'neutral_quality' not in self.fixed_params:
            self.params['neutral_quality'] = 3.0
        else:
            self.params['neutral_quality'] = self.fixed_params['neutral_quality']
        self.form_perception_of_quality()
        product_is_purchased = self.make_purchase()
        self.purchase_count += product_is_purchased * 1.0
        self.purchase_decisions.append(product_is_purchased)
        product_review = self.evaluate_product()

        if self.decide_to_rate(product_review):
            self.reviews.append(product_review)
            self.avg_reviews.append(np.mean(self.reviews))
            self.histogram_reviews[product_review - 1] += 1
            a_product_is_reviewed = True
        else:
            a_product_is_reviewed = False

        self.customer_count += 1

        return a_product_is_reviewed

    def generateTimeseries(self, theta, get_percieved_qualities_and_avg_reviews=False, do_not_return_df=False):

        # conditioned on the fixed_params
        self.set_random_params(theta)  # The random parameter that is the subject of inference is set here.
        # This parameter determines the true label for the generated time series (example).
        # The distribution according to which the parameter is randomized is our prior on it

        self.init_reputation_dynamics()
        timeseries = []

        while len(timeseries) < self.params['total_number_of_reviews']:
            a_product_is_reviewed = self.step()

            if a_product_is_reviewed:
                if self.params['input_type'] == 'averages':
                    timeseries.append(self.avg_reviews[-1])
                elif self.params['input_type'] == 'histograms':
                    histogram = copy.deepcopy(self.histogram_reviews)
                    if self.params['input_histograms_are_normalized'] and (sum(histogram) > 0):
                        histogram = list(np.array(histogram) / (1.0 * sum(histogram)))
                    timeseries.append(histogram)
                elif self.params['input_type'] == 'kurtosis':
                    histogram = copy.deepcopy(self.histogram_reviews)
                    if (sum(histogram) > 0):
                        histogram = list(np.array(histogram) / (1.0 * sum(histogram)))
                    kurtosis = st.kurtosis(histogram, fisher=False, bias=True)
                    timeseries.append(kurtosis)

        if do_not_return_df:
            df = timeseries
        else:
            df = pd.DataFrame(timeseries)

        if get_percieved_qualities_and_avg_reviews:
            return df, self.avg_reviews, self.percieved_qualities
        else:
            return df

    def genTorchSample(self):
        # implement these if neural network in inference not for ABC
        pass

    def genTorchDataset(self, dataset_size=1000, filename='dataset.pkl', LOAD=False, SAVE=False):
        # implement these if neural network in inference not for ABC
        pass