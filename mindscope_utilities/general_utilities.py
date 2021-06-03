import pandas as pd
import numpy as np


def event_triggered_response(data, x, y, event_times, t_before=1, t_after=1, step_size=0.01, endpoint=True, output_format='tidy'):
    '''
    Slices a timeseries relative to a given set of event times to build an event-triggered response.

    For example, if we have a response of a sensory neuron, along the times of sensory events that elicit a response in that neuron,
    this function will return response in a time window surrounding each event.

    The times of the events need not align with the measured times of the neural data. Relative times will be calculated by linear interpolation.

    Parameters:
    -----------
    data: Pandas.DataFrame
        Input dataframe in tidy format
    x : string
        Name of column in data to use as x-data
    y : string
        Name of column to use as y-data
    event_times: list or array of floats
        Times of events of interest. Values in column specified by `y` will be sliced and interpolated relative to these times
    t_before : float
        time before each of event of interest to include in each slice
    t_after : float
        time after each event of interest to include in each slice
    step_size : float
        desired step size of output (input data will be interpolated to this step size)
    endpoint : Boolean
        Passed to np.linspace to calculate relative time
        If True, stop is the last sample. Otherwise, it is not included. Default is True
    output_format : string
        'wide' or 'tidy' (default = 'tidy')
        if 'tidy'
            One column representing time
            One column representing event_number
            One column representing event_time
            One row per observation (total rows = len(time) x len(event_times))
        if 'wide', output format will be:
            time as indices
            One row per interpolated timepoint
            One column per event, with column names titled event_{EVENT NUMBER}_t={EVENT TIME}
        
    Returns:
    --------
    Pandas.DataFrame
        See description in `output_format` section above

    Examples:
    ---------
    An example use case, recover a sinousoid from noise:
    
    First, define a time vector
    >>> t = np.arange(-10,110,0.001)

    Now build a dataframe with one column for time, and another column that is a noise-corrupted sinuosoid with period of 1
    >>> data = pd.DataFrame({
            'time': t,
            'noisy_sinusoid': np.sin(2*np.pi*t) + np.random.randn(len(t))*3
        })

    Now use the event_triggered_response function to get a tidy dataframe of the signal around every event
    Events will simply be generated as every 1 second interval starting at 0, since our period here is 1
    >>> etr = event_triggered_response(
            data,
            x = 'time',
            y = 'noisy_sinusoid',
            event_times = np.arange(100),
            t_before = 1,
            t_after = 1,
            step_size = 0.001
        )
    Then use seaborn to view the result
    We're able to recover the sinusoid through averaging
    >>> import matplotlib.pyplot as plt
    >>> import seaborn as sns
    >>> fig, ax = plt.subplots()
    >>> sns.lineplot(
            data = etr,
            x='time',
            y='noisy_sinusoid',
            ax=ax
        )
    '''

    _d = {'time': np.linspace(-t_before, t_after, int((t_before + t_after) / step_size + int(endpoint)), endpoint = endpoint)}
    for ii, event_time in enumerate(np.array(event_times)):

        data_slice = data.query("{0} > (@event_time - @t_before) and {0} < (@event_time + @t_after)".format(x))
        x_slice = data_slice[x] - event_time
        y_slice = data_slice[y]

        _d.update({'event_{}_t={}'.format(ii, event_time): np.interp(_d['time'], x_slice, y_slice)})

    wide_etr = pd.DataFrame(_d)
    if output_format == 'wide':
        return wide_etr.set_index('time')
    elif output_format == 'tidy':
        tidy_etr = wide_etr.melt(id_vars='time')
        tidy_etr['event_number'] = tidy_etr['variable'].map(lambda s: s.split('event_')[1].split('_')[0])
        tidy_etr['event_time'] = tidy_etr['variable'].map(lambda s: s.split('t=')[1])
        return tidy_etr.drop(columns=['variable']).rename(columns={'value': y})
