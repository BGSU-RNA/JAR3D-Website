"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from JAR3Dresults import views
from JAR3Dresults.models import Query_sequences

class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)

class FungalSeqTest(TestCase):
    def setUp(self):
        self.ss = '..((((...((((((.......((...........((((..((((.....(((((.....(((((...((((((.......)))))).......((((((((((((((....((((((...))))))))((((..(((.(((.(((((((.....((.((((((.......(((((....))))).)))))).)).)).......))))))))....)))..)))).))))).)))).)))(((((.(((...((((((((((((((.........................(((((((((((.((..(((......))))))))))))))))(((((((((...((((((.....))))))...))))))).))((((((......))))))))))))))).............)))))...)))))))).......................)))))........)))))....))))..)))).))......))))))))))....((((....((((..........................((.(((..(((.(((..........)))......)))..))).))....))))....))))......................'
        self.seq = ['GUGAGU---GACCUCU-UCUUUCCU-CUACUCGUUUCGCACCCCACCA-CCCAAUUUUCUGGGGGCUCUCUCCAA-CCUUAUGGAGAACCCCAAACCCGCACUGCGUCUGUU-CUCGACAAUCGA-GACGUUCUUCCACCCGUGACGAGG------UCCGCGCGCG-UUUUCGAUCGCUUGAUCGCCGCGUGGA--CCGCUGCAUACGUCCGGUC-AUGGUUGGACGCGCGGUUGUGUGGUGAAAUGGGGGGCUGAGCGAGGAGUGCGGAAAAGAC-AGCAGUAUAUCCCUCUGGGAGCUG-------------------------------CAUGGUUGGAUAACCGACUGCACUCGCUGUGACGCAGUUUGAGUGGCAUGUC---GGCGAUGCACUUUUUA------CUCGAUUCACGUAGCCCCCUGUGUAACCGUUUUCAGCGUUGUACCCGUUGAU---------------UGGGACACAGACAACGCGCCACCUUCCAUGUUCGAGCG------------------------------CACGCUGACAUUUUGGUCUCUAUAUCCUU--------------CUCAUCCCUCGAAUUGGAUCGUUG--------CAUAAUGUAAG']
        validator = views.JAR3DValidator()
        fasta = []
        (self.loops, self.indices) = validator.isfolded_extract_loops(self.ss,self.seq)
        self.query_info = validator.make_query_info('1','1','1')
        self.query_seqs = validator.make_query_sequences(self.loops, fasta, '1')
        self.query_inds = validator.make_query_indices(self.indices,'1')
        [seq.save() for seq in self.query_seqs]
        self.query_seqs_db = Query_sequences.objects.filter(query_id='1')
    def test_fungal_ss_reader(self):    
        self.assertEqual(len(self.loops.keys()),35)
    def test_fungal_dict_convert(self):    
        self.assertEqual(len(self.query_seqs),35)
    def test_fungal_db_saver(self):    
        self.assertEqual(len(self.query_seqs_db),35)

class ViroidSeqTest(TestCase):
    def setUp(self):
        self.ss = '.((((((((.((.((((((((.(.((((.((((((..(((((.((((((...(((........(((((((((((.((...((((((((..((((((((.....(((((((((.(.((((...((((..(((((((.(((.((..((((.((.((((((.....((((..((((.(((((....)))))...))))..)))).....))))).))).)))).))..))).))))))).))))))).).))))))))))......))))).)))..)..))))))))))))))..)))))).........)))...)).)))).)))).).))))))..)))))..)))))))))))))))))).'
        self.seq = ['CGGAACUAAACUCGUGGUUCCUGUGGUUCACACCUGACCUCCUGAGCAGAAAAGA-AAAAAGAAGGCGGCUCGGAGGAGCGCUUCAGGGAUCCCCGGGGAAACCUGGAGCGAACUGGCA-AUAAGGACGGUGGGGAGUGCCC-AGCGGCCGACAGGAGUAAUUCCCGCCGAAACAGGGUUUUCACCCUUCCUUUCUUCGGGUGUCCUUCCUCGCGCCCGCAGGACCACCCCUCGCCCCCUUUGCGCUGUCGCUUCGGAUAUUACCCGGUGGAAACAACUGAAGCUCCCGAGAACCGCUUUUUCUC-UAUCUUUCUUUGCUUCGGGGCGAGGGUGUUUAGCCCUUGGAACCGCAGUUGGUUCCU']
        validator = views.JAR3DValidator()
        fasta = []
        (self.loops, self.indices) = validator.isfolded_extract_loops(self.ss,self.seq)
        self.query_info = validator.make_query_info('1','1','1')
        self.query_seqs = validator.make_query_sequences(self.loops, fasta, '1')
        self.query_inds = validator.make_query_indices(self.indices,'1')
        [seq.save() for seq in self.query_seqs]
        self.query_seqs_db = Query_sequences.objects.filter(query_id='1')
    def test_fungal_ss_reader(self):    
        self.assertEqual(len(self.loops.keys()),34)
    def test_fungal_dict_convert(self):    
        self.assertEqual(len(self.query_seqs),33)
    def test_fungal_db_saver(self):    
        self.assertEqual(len(self.query_seqs_db),33)

class AlignmentMakerTest(TestCase):
    def setUp(self):
        self.single_loop = 'CAG*CGG\n'
        self.fasta_loop = '>Loop1\nCAG*CGG\n'
        self.ss = '((...))\nCCAAAGG\n'
        self.fasta_ss = '((...))\n>Sequence1\nCCAAAGG\n'
        self.parsed_single_loop = views.make_input_alignment(self.single_loop,'isNoFastaSingleLoop')
        self.parsed_fasta_loop = views.make_input_alignment(self.fasta_loop,'isFastaSingleLoop')
        self.parsed_ss = views.make_input_alignment(self.ss,'isNoFastaSingleLoop')
        self.parsed_fasta_ss = views.make_input_alignment(self.fasta_ss,'isFastaSingleLoop')
    def test_single_loop:
        self.assertEqual(self.single_loop,self.parsed_single_loop)
    def test_fasta_loop:
        self.assertEqual(self.fasta_loop,self.parsed_fasta_loop)
    def test_ss:
        self.assertEqual(self.parsed_ss,'  1    2    3    4    5    6    7  \n  C    C    A    A    A    G    G  \n')
    def test_fasta_ss:
        self.assertEqual(self.parsed_fasta_ss,'  1    2    3    4    5    6    7  \n>Sequence1\n  C    C    A    A    A    G    G  \n')