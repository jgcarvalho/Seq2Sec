import torch
from seq2sec.data import AA, PAD, INPUT_CODE
from sys import argv
import numpy as np
from seq2sec.model import load

class Protein(object):
    def __init__(self, fasta_file):
        s = self._read_fasta_file(fasta_file)
        assert(self._is_ok(s))
        self.seq = s 
        # self.one_hot = self._encode_aa(s) 
        self.prediction = {}
        self.probabilities = {}
        self.steps = {}
        
    def predict_with(self, model_func):
        # y_pred = model_func(self._encode_aa(self.seq))
        pred = model_func(self._pad_input(self._seq2int(self.seq)))
        self.probabilities = {k:np.transpose(np.squeeze(pred[k])[:,:,PAD:-PAD][-1,:,:]) for k in pred}
        # # remove sequence padding
        self.prediction = {k: self._prob2ss(self.probabilities[k]) for k in self.probabilities}
        # # transpose axis to create C matrix LxD where C is the number of classes, L is the length 
        # # of the protein sequence and D is depth of the resnet (number of blocks)
        self.steps = {k: np.transpose(np.squeeze(pred[k])[:,:,PAD:-PAD], axes=[1,2,0]) for k in pred}

    def plot_probs(self):
        pass

    def plot_steps(self):
        pass

    @staticmethod 
    def _prob2ss(prob):
        # number of classes (types of secondary structure)
        n_c = prob.shape[1]
        c = ['H', 'E', 'C']
        if n_c == 4:
            c = ['H', 'E', 'C', 'T']
        elif n_c == 8: 
            c = ['H', 'G', 'I', 'E', 'C', 'T', 'B', 'S']
        idx = prob.argmax(axis=1)
        return ''.join([c[i] for i in idx])

    @staticmethod
    def _read_fasta_file(fn):
        with open(fn, 'r') as f:
            seq = ""
            for l in f.readlines():
                if l.startswith('>'): 
                    continue
                else:
                    seq += l.strip()
        return seq.upper()

    @staticmethod 
    def _is_ok(sequence):
        for i in sequence:
            if not i in AA.__members__:
                print("Error: {} is not a valid aminoacid code")
                return False
        return True

    @staticmethod
    def _seq2int(seq):
        code = np.zeros(len(seq), dtype=np.int)
        for i, aa in enumerate(seq):
            code[i] = AA[aa].value
        return code

    @staticmethod
    def _pad_input(x):
        idx = np.pad(x, (PAD,PAD), 'constant', constant_values=(AA['before'].value, AA['after'].value))
        m = torch.zeros((1, INPUT_CODE, len(x)+(2*PAD)), requires_grad=False)
        m[0, idx, np.arange(len(x)+(2*PAD))] = 1
        return m

    def plot_probs(self):
        pass

    def plot_steps(self):
        pass


    def iplot_probabilities(self):
        import plotly.graph_objs as go
        from plotly.offline import download_plotlyjs, init_notebook_mode, iplot
        init_notebook_mode(connected=True)

        x = [i for i in range(len(self.seq))]
        y0 = self.probabilities[:,0]
        y1 = self.probabilities[:,1]
        y2 = self.probabilities[:,2]
        
        # p_h = go.Bar(x=x, y=y0, opacity=0.4, name='Helix', marker=dict(color='#ff0000'))
        # p_e = go.Bar(x=x, y=y1, opacity=0.4, name='Strand', marker=dict(color='#0000ff'))
        # p_c = go.Bar(x=x, y=y2, opacity=0.4, name='Coil', marker=dict(color='#00ff00'))
        # p_h = go.Bar(x=x, y=y0, opacity=0.4, name='Helix')
        # p_e = go.Bar(x=x, y=y1, opacity=0.4, name='Strand')
        # p_c = go.Bar(x=x, y=y2, opacity=0.4, name='Coil')
        # p_h = go.Scatter(x=x, y=y0, name='Helix', line=dict(shape='hvh'))
        # p_e = go.Scatter(x=x, y=y1, name='Strand', line=dict(shape='hvh'))
        # p_c = go.Scatter(x=x, y=y2, name='Coil', line=dict(shape='hvh'))

        n_c = self.probabilities.shape[1]
        data = []
        if n_c == 3 or n_c == 4:
            data.append(go.Bar(x=x, y=self.probabilities[:,0], opacity=0.4, name='Helix'))
            data.append(go.Bar(x=x, y=self.probabilities[:,1], opacity=0.4, name='Strand'))
            data.append(go.Bar(x=x, y=self.probabilities[:,2], opacity=0.4, name='Coil'))
            if n_c == 4:
                data.append(go.Bar(x=x, y=self.probabilities[:,3], opacity=0.4, name='Turn'))
        elif n_c == 8:
            data.append(go.Scatter(x=x, y=self.probabilities[:,0], line=dict(shape='hvh'), name='alpha Helix')) #H
            data.append(go.Scatter(x=x, y=self.probabilities[:,1], line=dict(shape='hvh'), name='3 Helix')) #G
            data.append(go.Scatter(x=x, y=self.probabilities[:,2], line=dict(shape='hvh'), name='5 Helix')) #I
            data.append(go.Scatter(x=x, y=self.probabilities[:,3], line=dict(shape='hvh'), name='Strand')) #E
            data.append(go.Scatter(x=x, y=self.probabilities[:,4], line=dict(shape='hvh'), name='Coil')) #C
            data.append(go.Scatter(x=x, y=self.probabilities[:,5], line=dict(shape='hvh'), name='Turn')) #T
            data.append(go.Scatter(x=x, y=self.probabilities[:,6], line=dict(shape='hvh'), name='beta Bridge')) #B
            data.append(go.Scatter(x=x, y=self.probabilities[:,7], line=dict(shape='hvh'), name='Bend')) #S
            # # Alternative bar
            # data.append(go.Bar(x=x, y=self.probabilities[:,0], opacity=0.2, name='alpha Helix')) #H
            # data.append(go.Bar(x=x, y=self.probabilities[:,1], opacity=0.2, name='3 Helix')) #G
            # data.append(go.Bar(x=x, y=self.probabilities[:,2], opacity=0.2, name='5 Helix')) #I
            # data.append(go.Bar(x=x, y=self.probabilities[:,3], opacity=0.2, name='Strand')) #E
            # data.append(go.Bar(x=x, y=self.probabilities[:,4], opacity=0.2, name='Coil')) #C
            # data.append(go.Bar(x=x, y=self.probabilities[:,5], opacity=0.2, name='Turn')) #T
            # data.append(go.Bar(x=x, y=self.probabilities[:,6], opacity=0.2, name='beta Bridge')) #B
            # data.append(go.Bar(x=x, y=self.probabilities[:,7], opacity=0.2, name='Bend')) #S

        
            # H = α-helix
            # B = residue in isolated β-bridge
            # E = extended strand, participates in β ladder
            # G = 3-helix (310 helix)
            # I = 5 helix (π-helix)
            # T = hydrogen bonded turn
            # S = bend 

        # data = [p_h, p_e, p_c]
        layout = go.Layout(
            barmode='overlay', 
            yaxis=dict(
                range=[0, 1],
                hoverformat = '%'
            ),
            xaxis=go.layout.XAxis(
                ticktext=list(self.seq),
                tickvals=x,
                tickangle=0,
                tickfont=dict(
                    family='Courier, mono',
                    color='black'
                ),
                ticks='outside',
                ticklen=2,
            ),
            
        )
        fig = go.Figure(data=data, layout=layout )

        iplot(fig)



def hello():
    print('Hello!')

if __name__ == "__main__":
    net = load('../models/teste_4.pth')
    


    # # read fasta
    # # x = torch.randn((1,22,10))
    # p = Protein("../fasta_sequences/start2fold/STF0001.fasta")
    # p.predict_with(net.predict)
    # print(p.probabilities)
    # print(p.probabilities.shape)
    # print(p.steps.shape)
    # # x = p.one_hot
    # # print(x)
    # # print(x.shape)
    # # p.probabilities = net.predict(x)
    # # print(pred)
    # # print(pred.shape)

    # # apply model to fasta and create a dataframe
