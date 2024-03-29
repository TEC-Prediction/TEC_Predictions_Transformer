import torch
import torch.nn as nn
import torch.nn.functional as F
import math
import wandb

class Transformer_encoder(nn.Module):
    def __init__(self, config, shaper, criterion=None):
        super(Transformer_encoder, self).__init__()
        self.config = config
        self.shaper = shaper
        self.criterion = criterion
        input_dim = self.shaper.get_input_dim()
        tec_output_dim = self.shaper.get_tec_output_dim()
        
        self.device = config['global']['device']
        self.input_time_step = config.getint('model', 'input_time_step')
        self.output_time_step = config.getint('model', 'output_time_step')
        self.hidden_size = config.getint('model', 'hidden_size')
        self.num_layer = config.getint('model', 'num_layer')
        self.dropout = config.getfloat('model', 'dropout')
        
        self.embedding = nn.Linear(input_dim, self.hidden_size)
        self.pos_encoder = PositionalEncoding(d_model=self.hidden_size)
        self.encoder_layer = nn.TransformerEncoderLayer(d_model=self.hidden_size, nhead=8,\
                            dropout=self.dropout, norm_first=True, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(self.encoder_layer, num_layers=self.num_layer)
        self.fc = nn.Linear(self.hidden_size, tec_output_dim) # global prediction
        self.init_weights()
    
    def init_weights(self):
        initrange = 0.1
        self.embedding.bias.data.zero_()
        self.embedding.weight.data.uniform_(-initrange, initrange)
        self.fc.bias.data.zero_()
        self.fc.weight.data.uniform_(-initrange, initrange)

    def _generate_square_subsequent_mask(self, sz):
        mask = (torch.triu(torch.ones(sz, sz)==1).transpose(0, 1))
        mask = mask.float().masked_fill(mask == 0, float('-inf')).masked_fill(mask == 1, float(0.0))
        return mask

    def forward(self, x, **y):
        # x: (batch_size, input_d)
        # print(x.shape)
        embedded = self.embedding(x)
        # print(embedded.shape)
        pos_encoder_out = self.pos_encoder(embedded)
        # mask = self._generate_square_subsequent_mask(pos_encoder_out.size(1)).to(self.device)
        # trans_output = self.transformer_encoder(pos_encoder_out, mask) # batch_size, seq_len, hidden_size
        # print(pos_encoder_out.shape)
        trans_output = self.transformer_encoder(pos_encoder_out) # batch_size, seq_len, hidden_size
        # trans_output = trans_output # batch_size, seq_len, hidden_size
        # print(trans_output.shape)
        fc_out = F.relu(self.fc(trans_output)) # batch_size, seq_len, 71*72
        # print(fc_out.shape)
        # mean pooling
        # pred = torch.mean(fc_out, dim=1) # batch_size, 71*72
        # pred = fc_out[:,-1] # batch_size, 71*72
        pred = self.shaper.model_tec_drop(fc_out)
        # print(pred.shape)
        
        loss = self.criterion(pred, y['tec'])
        return pred, {'loss':loss}\
            if self.criterion != None else pred
    
    def record(self, loss, mode):
        wandb.log({f'{mode}_loss':loss['loss']})
        
class PositionalEncoding(nn.Module):

    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()       
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        #pe.requires_grad = False
        self.register_buffer('pe', pe)

    def forward(self, x):
        return x + self.pe[:x.size(0), :]