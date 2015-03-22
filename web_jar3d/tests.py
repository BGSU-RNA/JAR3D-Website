"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
import views
from models import Query_sequences

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
