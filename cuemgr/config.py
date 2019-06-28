config = {
  'LightArms': [
    #{'address':'10.0.0.167', 'numChannels':12},
    
    # this is how you would define a light arm
    {'address':'10.0.0.30', 'numChannels':12, 'numServos':2, 'inversions':[False, False]},
    {'address':'10.0.0.31', 'numChannels':12, 'numServos':2, 'inversions':[False, False]},
    {'address':'10.0.0.63', 'numChannels':12, 'numServos':2, 'inversions':[False, False]},
  ],

  'DMX': {'universes': [1]},
  
  'Prinboo': {}, #TODO
}


