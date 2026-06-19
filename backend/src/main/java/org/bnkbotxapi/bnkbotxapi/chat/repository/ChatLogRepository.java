package org.bnkbotxapi.bnkbotxapi.chat.repository;

import org.bnkbotxapi.bnkbotxapi.chat.domain.ChatLogEntity;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ChatLogRepository extends JpaRepository<ChatLogEntity, Long> {

    List<ChatLogEntity> findTop30ByAccountIdOrderByChatLogIdDesc(Long accountId);
}
