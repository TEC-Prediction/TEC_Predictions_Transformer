from .LSTMTEC import LSTMTEC
from .LSTM_TEC import LSTM_TEC
from .LSTM_seq2seq import LSTM_Seq2Seq
import torch
from pathlib import Path
def initialize_model(config, arg, *args, **kwargs):
    model_list = {
        'LSTM_TEC':LSTMTEC,
        'LSTM_TEC_2SW':LSTMTEC,
        'LSTM_Seq2Seq_TEC': LSTM_Seq2Seq,
    }
    model_ft_list = {
        'LSTM_TEC' : 1,
        'LSTM_TEC_2SW' : 3,
        'LSTM_Seq2Seq_TEC' : 1,
    }
    
    feature_dim = model_ft_list[model_name]
    
    model_name = config['model']['model_name']
    if arg.mode == 'train':
        return model_list[model_name](config, feature_dim, *args, **kwargs)
    else: # test
        model = model_list[model_name](config, feature_dim, *args, **kwargs)
        model.load_state_dict(torch.load(Path(arg.record) / 'best_model.pth'))
        return model
    