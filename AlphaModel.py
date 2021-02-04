from datetime import timedelta

class FundamentalFactorAlphaModel(AlphaModel):
    def __init__(self, num_fine, quality_weight, value_weight, size_weight):
        self.lastMonth = -1
        self.longs = [] #list that would hold the stocks in we want to buy
        self.num_fine = num_fine # the past argument
        self.period = timedelta(31)#time frame that holds each stock position
        
        weights = [quality_weight, value_weight, size_weight]
        weights = [float(i)/sum(weights) for i in weights]
        
        self.quality_weight = weights[0]
        self.value_weight = weights[1]
        self.size_weight = weights[2]
        
    
    def Update(self, algorithm, data):#if a new price is called it will send the trade signals
        if algorithm.Time.month == self.lastMonth:
            return[]
        self.lastMonth = algorithm.Time.month
        
        insights = []
        
        for security in algorithm.Portfolio.Values:
            if security.Invested and security.Symbol not in self.longs:
                insights.append(Insight(security.Symbol, self.period, InsightType.Price, InsightDirection.Flat, 
                                                None, None, None, None))
                                                
        length = len(self.longs)
        for i in range(length):
            insights.append(Insight(self.longs[i], self.period, InsightType.Price, InsightDirection.Up,
                                        None, (length - i)**2, None, (length - i)**2))
                                        
        return insights
                                        
    
    def OnSecuritiesChanged(self, algorithm, changes):
        added = [x for x in changes.AddedSecurities]
        
        quality_scores = self.Scores(added, [(lambda x : x.Fundamentals.OperationRatios.GrossMargin.Value, True, 2),
                                            (lambda x : x.Fundamentals.OperationRatios.QuickRatio.Value, True, 1),
                                            (lambda x : x.Fundamentals.OperationRatios.DebttoAssets.Value, False, 2)])
        
        
        value_scores = self.Scores(added, [(lambda x : x.Fundamentals.ValuationRatios.BookValuePerShare, True, 0.5),
                                            (lambda x : x.Fundamentals.ValuationRatios.CashReturn, True, 0.25),
                                            (lambda x : x.Fundamentals.ValuationRatios.EarningYield, True, 0.25)])
                                            
                                            
        size_scores = self.Scores(added, [(lambda x : x.Fundamentals.MarketCap, False, 1)])
        
        scores = {}
        
        for symbol, value in quality_scores.items():
            quality_rank = value
            value_rank = value_scores[symbol]
            size_rank = size_scores[symbol]
            scores[symbol] = quality_rank * self.quality_weight + value_rank * self.value_weight + size_rank * self.size_weight
            
            
        sorted_stock = sorted(scores.items(), key = lambda tup: tup[1], reverse=False)
        sorted_symbol = [tup[0] for tup in sorted_stock][:self.num_fine]
        
        self.longs = [security.Symbol for security in sorted_symbol]
        
        algorithm.Log(", ".join([str(x.Symbol.Value) + ": " + str(scores[x]) for x in sorted_symbol]))
        
        
        
    #Takes two values the list of securities which is in the added variable and a list of tuples with three elements each    
    def Scores(self, added, fundamentals):
        length = len(fundamentals)
        if length == 0:
            return {}
            
        scores = {}
        sortedBy = []
        rank = [0 for _ in fundamentals]
        
        weights = [tup[2] for tup in fundamentals]
        weights = [float(i)/sum(weights) for i in weights]
        
        for tup in fundamentals:
            sortedBy.append(sorted(added, key=tup[0], reverse = tup[1]))
            
        for index, symbol in enumerate(sortedBy[0]):
            rank[0] = index
            for j in range(1, length):
                rank[j] = sortedBy[j].index(symbol)
                
            score = 0
            for  i in range (length):
                score += rank[i] * weights[i]
            scores[symbol] = score
            
        return scores
