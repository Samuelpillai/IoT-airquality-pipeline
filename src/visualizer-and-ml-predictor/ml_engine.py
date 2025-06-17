from prophet import Prophet

class MLPredictor:
    def __init__(self, data_df):
        self.__train_data = self.__convert_col_name(data_df)
        self.__trainer = Prophet(change_point_prior_scale=12)
   
    def train(self):
        self.__trainer.fit(self.__train_data)

    def __convert_col_name(self, data_df):
        data_df.rename(columns={'Timestamp': 'ds', 'y': 'y'}, inplace=True)
        return data_df
    
    def __makefuture(self, periods=15):
        future = self.__trainer.make_future_dataframe(periods=periods)
        return future
    
    def predict(self):
        future = self.__makefuture()
        forecast = self.__trainer.predict(future)
        return forecast
    
    def plot_results(self, forecast):
        fig = self.__trainer.plot(forecast, figsize=(15, 6))
        return fig