from pymongo import MongoClient, errors

class MongoConnect:
    """
    Class to store miscellaneous data in MongoDB such as clustering results,
    strategy performance and other miscellaneous data.
    """
    def __init__(self, mongodb_url="mongodb://localhost:27017/", cluster_collection="cluster_results",
                  pairs_collections="pairs_results", strategy_collection="strategy_parameters",
                  strategy_results_collection="strategy_results", strategy_trades_collection="strategy_trades"):
        self.client = MongoClient(mongodb_url)
        self.db = self.client["equity_data"]

        self.cluster_collection = self.db[cluster_collection]
        self.pairs_collection = self.db[pairs_collections]
        self.strategy_collection = self.db[strategy_collection]
        self.strategy_results_collection = self.db[strategy_results_collection]
        self.strategy_trades_collection = self.db[strategy_trades_collection]

        try:
            self.db.create_collection(cluster_collection)
            self.db.create_collection(strategy_collection)
            self.db.create_collection(pairs_collections)

        except errors.CollectionInvalid:
            pass

    def post_clustering_results(self, method, start_date, end_date, cluster_dict):
        """
        Post clustering results to MongoDB.

        Parameters
        ----------
        method : str
            Clustering method.
        start_date : str
            Start date.
        end_date : str
            End date.
        """
        criteria = {
            "method": method,
            "start_date": start_date,
            "end_date": end_date
        }
        new_data = { "$set": {
            "method": method,
            "start_date": start_date,
            "end_date": end_date,
            "cluster_dict": cluster_dict
        }}
        self.cluster_collection.update_one(criteria, new_data, upsert=True)

    def get_clustering_results(self, method, start_date, end_date):
        """
        Get clustering results from MongoDB.

        Parameters
        ----------
        method : str
            Clustering method.
        start_date : str
            Start date.
        end_date : str
            End date.

        Returns
        -------
        dict
            Clustering results.
        """
        return self.cluster_collection.find_one({
            "method": method,
            "start_date": start_date,
            "end_date": end_date
        })["cluster_dict"]
    
    def get_cluster(self, method, cluster, start_date, end_date):
        """
        Get cluster from MongoDB.

        Parameters
        ----------
        method : str
            Clustering method.
        cluster : str
            Cluster.
        start_date : str
            Start date.
        end_date : str
            End date.

        Returns
        -------
        list
            List of tickers in cluster.
        """
        return self.cluster_collection.find_one({
            "method": method,
            "start_date": start_date,
            "end_date": end_date
        })["cluster_dict"][cluster]
    
    def get_all_clustering_results(self):
        """
        Get all possible method, start_date, end_date combinations from MongoDB.
        
        Returns
        -------
        list
            List of method, start_date, end_date combinations.
        """
        return self.cluster_collection.find({}, {"method": 1, "start_date": 1, "end_date": 1, "_id": 0})
    
    def post_pairs_results(self, method, chosen_cluster, start_date, end_date, pairs):
        """
        Post pairs results to MongoDB.

        Parameters
        ----------
        method : str
            Clustering method.
        chosen_cluster : str
            Chosen cluster.
        start_date : str
            Start date.
        end_date : str
            End date.
        pairs : list
            List of pairs.
        """

        criteria = {
            "method": method,
            "chosen_cluster": chosen_cluster,
            "start_date": start_date,
            "end_date": end_date
        }
        new_data = { "$set": {
            "method": method,
            "chosen_cluster": chosen_cluster,
            "start_date": start_date,
            "end_date": end_date,
            "pairs": pairs
        }}
        self.pairs_collection.update_one(criteria, new_data, upsert=True)

    def get_pairs_results(self, method, chosen_cluster, start_date, end_date):
        """
        Get pairs results from MongoDB.

        Parameters
        ----------
        method : str
            Clustering method.
        chosen_cluster : str
            Chosen cluster.
        start_date : str
            Start date.
        end_date : str
            End date.

        Returns
        -------
        list
            List of pairs.
        """
        return self.pairs_collection.find_one({"method": method,"chosen_cluster": chosen_cluster,"start_date": start_date,"end_date": end_date})["pairs"]
    
    def get_all_pairs_results(self):
        """
        Get all possible method, chosen_cluster, start_date, end_date combinations from MongoDB.
        
        Returns
        -------
        list
            List of method, chosen_cluster, start_date, end_date combinations.
        """
        return self.pairs_collection.find({}, {"method": 1, "chosen_cluster": 1, "start_date": 1, "end_date": 1, "_id": 0})
    
    def post_strategy(self, ticker_1, ticker_2, method, start_training_date, end_training_date, start_date_trade, end_date_trade, hyperparameters, uuid, results, trades):
        """
        Posts list of trades to MongoDB.
        """
        self.post_strategy_parameters(ticker_1, ticker_2, method, start_training_date, end_training_date, start_date_trade, end_date_trade, hyperparameters, uuid, results, trades)
        self.post_strategy_results(uuid, results)
        self.post_strategy_trades(uuid, trades)

    def post_strategy_parameters(self, ticker_1, ticker_2, method, start_training_date, end_training_date, start_date_trade, end_date_trade, hyperparameters, uuid, results, trades):
        
        criteria = {
            "ticker_1": ticker_1,
            "ticker_2": ticker_2,
            "method": method,
            "start_training_date": start_training_date,
            "end_training_date": end_training_date,
            "start_date_trade": start_date_trade,
            "end_date_trade": end_date_trade,
            "hyperparameters": hyperparameters,
            "uuid": uuid
        }
        new_data = { "$set": {
            "ticker_1": ticker_1,
            "ticker_2": ticker_2,
            "method": method,
            "start_training_date": start_training_date,
            "end_training_date": end_training_date,
            "start_date_trade": start_date_trade,
            "end_date_trade": end_date_trade,
            "hyperparameters": hyperparameters,
            "uuid": uuid
        }}
        self.strategy_collection.update_one(criteria, new_data, upsert=True)

    def post_strategy_results(self, uuid, results):

        criteria = {
            "uuid": uuid
        }
        new_data = { "$set": {
            "uuid": uuid,
            "results": results
        }}
        self.strategy_results_collection.update_one(criteria, new_data, upsert=True)

    def post_strategy_trades(self, uuid, trades):
        criteria = {
            "uuid": uuid,
        }
        new_data = { "$set": {
            "uuid": uuid,
            "trades": trades
        }}
        self.strategy_trades_collection.update_one(criteria, new_data, upsert=True)
        
    def query_specific_strategy(self, ticker_1, ticker_2, method, start_training_date, end_training_date, start_date_trade, end_date_trade):
        criteria = {
            "ticker_1": ticker_1,
            "ticker_2": ticker_2,
            "method": method,
            "start_training_date": {"$gte": start_training_date},
            "end_training_date": {"$lte": end_training_date},
            "start_date_trade": {"$gte": start_date_trade},
            "end_date_trade": {"$lte": end_date_trade},
        }
        return [item["uuid"] for item in self.strategy_collection.find(criteria, {"uuid": 1})]


    def query_most_profitable(self, top_k):
        # Sort by profit in descending order and limit to top K results
        return [item["uuid"] for item in self.strategy_results_collection.find({}, {"uuid": 1}).sort("results.growth", -1).limit(top_k)]
    
    def query_by_tickers(self, ticker_1, ticker_2):
        criteria = {
            "$or": [
                {"ticker_1": ticker_1, "ticker_2": ticker_2},
                {"ticker_1": ticker_2, "ticker_2": ticker_1}
            ]
        }
        return [item["uuid"] for item in self.strategy_collection.find(criteria, {"uuid": 1})]
    
    def query_by_method(self, method):
        criteria = {
            "method": method
        }
        return [item["uuid"] for item in self.strategy_collection.find(criteria, {"uuid": 1})]
    
    def query_uuid(self, uuid):
        criteria = {
            "uuid": uuid
        }
        return self.strategy_collection.find(criteria),self.strategy_results_collection.find(criteria),self.strategy_trades_collection.find(criteria)