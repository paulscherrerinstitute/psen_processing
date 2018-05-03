FROM continuumio/miniconda3
RUN conda install -c paulscherrerinstitute psen_processing && conda update zeromq pyzmq mflow pyepics && conda clean --all && apt-get update && apt-get install vim
