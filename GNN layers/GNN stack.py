'''
GNN Stack Module
'''
import torch
from torch import nn
from torch.nn import functional as F
from GNN_Learning_PyG.cab3_1 import GraphSage
from GNN_Learning_PyG.cab3_2 import GAT
from torch_geometric.datasets import Planetoid
from torch_geometric.data import DataLoader


class GNNStack(torch.nn.Module):
    def __init__(self, input_dim, hidden_dim, output_dim, args, emb=False):
        '''
        ģ�ͽṹ�ĳ�ʼ��
        :param input_dim: ��������ά��
        :param hidden_dim: ���ز��ά��
        :param output_dim: ������ά��
        :param args: ��������
        :param emb: �Ƿ񷵻�Ƕ�룬Ĭ��false
        '''
        super(GNNStack, self).__init__()

        #  ��GraphSageģ�ͻ�GATģ������
        conv_model = self.build_conv_model(args.model_type)
        self.convs = nn.ModuleList()
        self.convs.append(conv_model(input_dim, hidden_dim))
        assert (args.num_layers >= 1), 'Number of layers is not >= 1'

        #  ѡ����ģ�ͽ�������
        for l in range(args.num_layers - 1):
            self.convs.append(conv_model(args.heads * hidden_dim, hidden_dim))

        #  ����ģ��
        self.post_mp = nn.Sequential(
            nn.Linear(args.heads * hidden_dim, hidden_dim),
            nn.Dropout(args.dropout),
            nn.Linear(hidden_dim, output_dim)
        )

        self.dropout = args.dropout
        self.nums_layers = args.num_layers
        self.emb = emb

    def build_conv_model(self, model_type):#  ���ݴ�����������Ͳ�ͬ�����ز�ͬ�Ļ���ģ��

        if model_type == 'GraphSage':
            return GraphSage
        elif model_type == 'GAT':
            return GAT

    def forward(self, data):
        x, edge_index, batch = data.x, data.edge_index, data.batch

        for i in range(self.nums_layers):
            x = self.convs[i](x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=self.dropout, training=self.training)

        x = self.post_mp(x)

        #  embΪtrue�򷵻ؽڵ�Ƕ���ʾ�����򷵻ؽڵ�Ԥ�������
        if self.emb == True:
            return x

        return F.log_softmax(x, dim=1)

    def loss(self, pred, label):
        return F.nll_loss(pred, label)


class objectview(object):
    def __init__(self, d):
        self.__dict__ = d


if __name__ == '__main__':
    # https://blog.csdn.net/PolarisRisingWar/article/details/116399648
    dataset = Planetoid(root='/tmp/cora', name='Cora')
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    args = {'model_type': 'GraphSage', 'dataset': 'cora', 'num_layers': 2, 'heads': 1, 'batch_size': 32,
            'hidden_dim': 32, 'dropout': 0.5, 'epochs': 500, 'opt': 'adam', 'opt_scheduler': 'none',
            'opt_restart': 0, 'weight_decay': 5e-3, 'lr': 0.01}
    args = objectview(args)

    model = GNNStack(dataset.num_features, 32, dataset.num_classes, args)

    for data in loader:
        output = model(data)
        print(output)
