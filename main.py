from Execution.ImmediateExecutionModel import ImmediateExecutionModel
from Risk.MaximumDrawdownPercentPerSecurity import MaximumDrawdownPercentPerSecurity

from AlphaModel import FundamentalFactorAlphaModel
#This algorithm bases its trading decisions on fundamental factors such as the size,quality and value of a given company. it takes the best 20 stocks

class UncoupledTachyonComputer(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2018, 5, 1)
        self.SetEndDate(2020, 5, 1)
        self.SetCash(100000)  # Set Strategy Cash
       
        self.SetExecution(ImmediateExecutionModel())

        self.SetPortfolioConstruction(InsightWeightingPortfolioConstructionModel())
        #stopRisk = 0.1 #yellow lines means lacking optomization
        stopRisk = self.GetParameter("stopRisk")
        if stopRisk is None:
            stopRisk = 1 #optomized methods
 #       self.SetRiskManagement(MaximumDrawdownPercentPerSecurity(stopRisk)) #closes a position if the loss proceeds a certain amount- fixed risk
        self.SetRiskManagement(TrailingStopRiskManagementModel(stopRisk))
        
        #filters out the 200 most liquid securities
        self.num_coarse = 200
        self.num_fine = 20 #the best 20 stocks
        self.lastMonth  = -1 #used to rebalance the portfolio once a month
        self.UniverseSettings.Resolution = Resolution.Daily #recieve daily data can be changed to minute aswell
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)
        
       #the weights of the socres they will be noramalized but relationship is important
        quality_weight = 2
        size_weight = 1
        value_weight = 2
        
        
        self.AddAlpha(FundamentalFactorAlphaModel(self.num_fine, quality_weight, size_weight, value_weight))
     
     
        self.Schedule.On(self.DateRules.Every(DayOfWeek.Monday), self.TimeRules.At(10, 30), self.Plotting)
    
    
    def Plotting(self):
        self.Plot("Positions", "Num", len([x.Symbol for x in self.Portfolio.Values if self.Portfolio[x.Symbol].Invested]))


    def CoarseSelectionFunction(self, coarse):
        if self.Time.month == self.lastMonth:
            return Universe.Unchanged
        self.lastMonth = self.Time.month
    
        selected = sorted([x for x in coarse if x.HasFundamentalData and x.Price >5],
                            key = lambda x : x.DollarVolume, reverse = True)
                            
        return [x.Symbol for x in selected[:self.num_coarse]]
    
    
    def FineSelectionFunction(self, fine): #filter out the securities that have a value greater than zero 
        filtered_fine = [x.Symbol for x in fine if x.OperationRatios.GrossMargin.Value > 0
                                        and x.OperationRatios.QuickRatio.Value> 0
                                        and x.OperationRatios.DebttoAssets.Value > 0
                                        and x.ValuationRatios.BookValuePerShare > 0
                                        and x.ValuationRatios.CashReturn >0
                                        and x.ValuationRatios.EarningYield >0
                                        and x.MarketCap > 0 ]

        return filtered_fine
