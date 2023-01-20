
use crate::sr;
use crate::armv8;

/// Clear all PMU registers.
pub fn clear_pmu_state() {
    unsafe { 
        sr::PMCR0_EL1::clear();
        sr::PMCR1_EL1::clear();
        sr::PMESR0_EL1::clear();
        sr::PMESR1_EL1::clear();
        sr::PMC0_EL1::clear();
        sr::PMC1_EL1::clear();
        sr::PMC2_EL1::clear();
        sr::PMC3_EL1::clear();
        sr::PMC4_EL1::clear();
        sr::PMC5_EL1::clear();
        sr::PMC6_EL1::clear();
        sr::PMC7_EL1::clear();
        sr::PMC8_EL1::clear();
        sr::PMC9_EL1::clear();
        armv8::isb();
    }
}

/// Representing some requested PMU configuration.
///
/// NOTE: There's probably a nicer way to do this ...
pub struct PmuConfig {
    pub en: [bool; 10],
    pub event: [Option<u8>; 10],
}
impl PmuConfig {
    pub fn new() -> Self {
        Self { en: [false; 10], event: [None; 10] }
    }
    /// Enable one of the counters. 
    pub fn enable(&mut self, idx: usize) {
        assert!(idx < 10);
        self.en[idx] = true;
    }
    /// Configure an event for a particular counter. 
    pub fn set_event(&mut self, idx: usize, event: u8) {
        assert!(idx < 10 && idx > 1);
        self.event[idx] = Some(event);
    }

    /// Retrieve the appropriate PMCR0_EL1 bits for this configuration.
    pub fn pmcr0_bits(&self) -> usize { 
        let mut bits = 0;
        for idx in 0..10 {
            if self.en[idx] {
                match idx {
                    0..=7 => bits |= (1 << idx),
                    8     => bits |= (1 << 32),
                    9     => bits |= (1 << 33),
                    _ => panic!(),
                }
            }
        }
        bits
    }

    /// Retrieve the appropriate PMCR1_EL1 bits for this configuration.
    pub fn pmcr1_bits(&self) -> usize {
        let mut bits = 0;
        for idx in 0..10 {
            if self.en[idx] {
                match idx {
                    0..=7 => bits |= (1 << idx) << 16,
                    8     => bits |= (1 << 48),
                    9     => bits |= (1 << 49),
                    _ => panic!(),
                }
            }
        }
        bits
    }

    /// Retrieve the appropriate PMESR0_EL1 bits for this configuration.
    pub fn pmesr0_bits(&self) -> usize { 
        let mut bits = 0;
        if let Some(evt) = self.event[2] { bits |= (evt as usize) << 0 }
        if let Some(evt) = self.event[3] { bits |= (evt as usize) << 8 }
        if let Some(evt) = self.event[4] { bits |= (evt as usize) << 16 }
        if let Some(evt) = self.event[5] { bits |= (evt as usize) << 24 }
        bits
    }

    /// Retrieve the appropriate PMESR1_EL1 bits for this configuration.
    pub fn pmesr1_bits(&self) -> usize { 
        let mut bits = 0;
        if let Some(evt) = self.event[6] { bits |= (evt as usize) << 0 }
        if let Some(evt) = self.event[7] { bits |= (evt as usize) << 8 }
        if let Some(evt) = self.event[8] { bits |= (evt as usize) << 16 }
        if let Some(evt) = self.event[9] { bits |= (evt as usize) << 24 }
        bits
    }
}

