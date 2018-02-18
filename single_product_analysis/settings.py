# Params and other settings are set here
# Settings are for the generative model as well as the inference engine


# The generative model settings

import pickle

observed_params = pickle.load(open('./data/'+'params_updated.pkl', 'rb'))

print(observed_params)

tracked_product_ID = 'B0067PLM5E'

def process_observed_params(observed_params, tracked_product_ID):
    params = dict()
    params['product_tracked'] = observed_params['product_indices'].index('B0067PLM5E')
    params['product_indices'] = [0]

    params['population_alpha'] = observed_params['alpha']

    params['price'] = observed_params['prices'][params['product_tracked']]

    params['product_features'] = dict.fromkeys(['RAM', 'BatteryLife', 'screen_size'])

    for i in params['product_features'].keys():
        params['product_features'][i] = observed_params[i][params['product_tracked']]

    params['population_beta'] = dict.fromkeys([s + '_beta' for s in params['product_features'].keys()])
    for i in params['population_beta'].keys():
        params['population_beta'][i] = observed_params[i]

    params['true_quality'] = observed_params['true_qualities'][params['product_tracked']]
    params['total_number_of_reviews'] = 40
    # params['input_type'] =  'kurtosis'
    # params['input_type'] = 'averages'
    params['input_type'] = 'histograms'
    # 'input_histograms_are_normalized': True,
    params['number_of_rating_levels'] = 5
    params['consumer_fit_std'] = observed_params['consumer_fit_std'][0]
    print(params)
    return params


params = process_observed_params(observed_params, tracked_product_ID)


# params = {'product_tracked': 0,
#           'prices': [10, 11, 12, 13],
#           'product_features': [1, 2, 3, 4],
#           'total_number_of_reviews': 20,
#           #'input_type': 'kurtosis',
#           # 'input_type': 'averages',
#           'input_type': 'histograms',
#           # 'input_histograms_are_normalized': True,
#           'number_of_rating_levels': 5,
#           }

# The inference engine settings

if params['input_type'] == 'histograms':
    number_of_features = 5# each point in the input time series is a oistogram comprised of
# five number for each of the five review levels (1,2,3,4,5)
    assert number_of_features == 5, 'wrong number of features'
else:
    number_of_features = 1# each point in the input time series is an average review
    assert number_of_features == 1, 'wrong number of features'

n_hidden = 8  # number of units in each layer of the recurrent unit

NUM_LAYERS = 3  # number of layers in each recurrent unit

OUTPUT_SIZE = 2  # output of the fully connected linear module at the end before the softmax

BATCH_SIZE = 4

# optimize parameters:

LEARNING_RATE = 0.003

WEIGHT_DECAY = 0.0001