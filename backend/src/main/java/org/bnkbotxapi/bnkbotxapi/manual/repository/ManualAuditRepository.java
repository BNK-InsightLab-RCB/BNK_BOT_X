package org.bnkbotxapi.bnkbotxapi.manual.repository;

import org.bnkbotxapi.bnkbotxapi.manual.domain.ManualAuditEntity;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ManualAuditRepository extends JpaRepository<ManualAuditEntity, Long> {
}
